# receipt_cpf_bot

Consulta a situação cadastral de um CPF no site público da Receita Federal, resolvendo o
hCaptcha da página automaticamente. Expõe a consulta por CLI e por API HTTP.

## Arquitetura

Três camadas, com dependência em uma direção só: `api` → `bot` → `core`.

```
api/     camada externa de comunicação (HTTP)
  main.py        aplicação FastAPI
  router.py      agregação das rotas
  routes/        cpf, health, metrics, diagnostics
  models/        contrato HTTP (Pydantic)
  services/      orquestra a consulta, métricas e mapeamento de erros
  dependencies/  autenticação por API key
  core/          settings, rate limit, métricas, handlers de erro

bot/     automação do navegador e da consulta
  query.py     orquestra a consulta ponta a ponta
  models.py    domínio (dataclasses)
  config.py    SOLVER_*, HEADLESS
  browser/     sessão do Chrome, fingerprint, DOM do hCaptcha
  captcha/     laço de resolução e cliente do solver
  lookup/      preenchimento do formulário e extração do HTML
  cli.py       entrada por linha de comando

core/    infraestrutura compartilhada pelas duas camadas
  logging_config.py
```

A `api` nunca é importada pelo `bot`. O solver de captcha é um serviço externo, acessado por
HTTP, então trocá-lo não exige mexer no bot.

## Requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Google Chrome instalado (o bot usa o canal `chrome`, não o Chromium empacotado)
- Um solver de hCaptcha acessível por HTTP
- Em servidor sem GPU: `xvfb` e `libgl1-mesa-dri` (ver
  [Renderização e deploy em servidor](#renderização-e-deploy-em-servidor))

## Configuração

```bash
cp .env.example .env
```

| Variável | Obrigatória | Padrão | Descrição |
| --- | --- | --- | --- |
| `SOLVER_URL` | sim | | URL base do solver de hCaptcha |
| `SOLVER_API_KEY` | sim | | Credencial enviada ao solver |
| `API_KEY` | sim | | Credencial exigida de quem chama esta API |
| `SOLVER_PATH` | não | `/api/v1/recognition/hcaptcha` | Caminho do endpoint de reconhecimento |
| `SOLVER_TIMEOUT_SECONDS` | não | `30` | Timeout de cada chamada ao solver |
| `HEADLESS` | não | `true` | Roda o Chrome sem janela |
| `CHROME_EXECUTABLE` | não | (canal `chrome` do sistema) | Caminho de um binário específico do Chrome |
| `CHROME_PROFILE_ROOT` | não | temp do sistema | Onde os perfis efêmeros do Chrome são criados |
| `API_V1_STR` | não | `/api/v1` | Prefixo das rotas da API |
| `PROJECT_NAME` | não | `receipt_cpf_bot` | Título exibido na documentação da API |

As três obrigatórias não têm padrão de propósito: sem elas o processo falha na inicialização,
em vez de errar depois com uma mensagem de rede confusa, ou, no caso de `API_KEY`, de subir
uma API aberta por engano. O `.env` não é versionado.

Gere a `API_KEY` com:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Instalação

```bash
uv sync
uv run patchright install chrome
```

## Uso

CLI:

```bash
uv run python -m bot.cli <cpf> <ddmmaaaa>
uv run python -m bot.cli 12345678901 07081978 --headless
```

API:

```bash
uv run uvicorn api.main:app --reload
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/cpf \
  -H 'Content-Type: application/json' \
  -H "X-API-Key: $API_KEY" \
  -d '{"cpf": "12345678901", "birth_date": "07081978"}'
```

A rota de consulta exige o header `X-API-Key`; sem ele, ou com chave errada, responde `401`.
`/health` fica aberta, para probe de liveness.

Resposta:

```json
{
  "metadata": {
    "request_id": "b3153446",
    "timestamp": "2026-09-21T00:56:51.112943Z",
    "source_data": {
      "source": "Receita Federal",
      "source_url": "https://servicos.receita.fazenda.gov.br/servicos/cpf/consultasituacao/ConsultaPublica.asp",
      "fields": [
        { "name": "cpf", "origin": "html", "value": "850.429.351-34" },
        { "name": "name", "origin": "html", "value": "FULANO DE TAL" },
        { "name": "status", "origin": "html", "value": "REGULAR" }
      ]
    }
  }
}
```

Cada campo carrega sua origem, e não só o valor: a consulta é uma extração de uma fonte
externa, então quem consome precisa saber de onde cada dado veio. A origem sai da propria
definicao do dominio, em `bot/models.py`.

## Rotas

| Rota | Auth | Descrição |
| --- | --- | --- |
| `POST /api/v1/cpf` | sim | Consulta a situação cadastral |
| `GET /api/v1/health` | não | Liveness, para probe da plataforma |
| `GET /api/v1/health/deep` | sim | Verifica se a Receita e o solver respondem |
| `GET /api/v1/metrics` | sim | Métricas Prometheus |
| `GET /api/v1/diagnostics` | sim | Sobe o navegador e reporta o ambiente que ele vê |

As rotas autenticadas exigem o header `X-API-Key` e respondem `401` sem ele. O limite é de
30 requisições por minuto, contadas por chave de API (6/min em `/diagnostics`, que sobe um
navegador a cada chamada).

Erros seguem o formato `{"detail": {"source": ..., "message": ...}}`:

| Status | Quando |
| --- | --- |
| `404` | CPF não consta na base da Receita |
| `422` | Payload inválido, ou data de nascimento que não bate com o CPF |
| `502` | Captcha rejeitado, ou resposta da Receita não reconhecida |
| `503` | CDN do hCaptcha limitando as requisições |


## Renderização e deploy em servidor

A Receita valida o token do hCaptcha e rejeita a consulta quando o WebGL é servido pelo
**SwiftShader**, o renderizador de software embutido no Chrome. Ele não aparece em máquina
de usuário real e denuncia automação. A mensagem nesse caso é
`O Anti-Robô não foi preenchido corretamente`, mesmo com o captcha resolvido.

O que decide não é headless ou headful, e sim qual renderizador o Chrome escolhe:

| Ambiente | Renderizador | Resultado |
| --- | --- | --- |
| Com GPU acessível | driver real (NVIDIA, etc.) | aceito |
| Sob Xvfb, sem GPU | Mesa/llvmpipe | aceito |
| Sem display X | SwiftShader | **rejeitado** |

Em servidor sem GPU, portanto, o Chrome precisa de um **display X virtual**. Sem ele não há
como alcançar o llvmpipe: o Chrome cai em SwiftShader com ou sem as flags. Headless e headful
funcionam igualmente, desde que dentro do Xvfb.

```bash
xvfb-run -a -s "-screen 0 1920x1080x24" uv run uvicorn api.main:app
```

O host precisa dos pacotes `xvfb` e `libgl1-mesa-dri` (o driver de software do Mesa).

Os ajustes que sustentam isso estão em `bot/browser/fingerprint.py`:

- `GL_ARGS`, aplicado nos dois modos, escolhe ANGLE sobre GL do sistema e desativa a
  blocklist de GPU: sem `--ignore-gpu-blocklist` o Chrome recusa o llvmpipe e volta ao
  SwiftShader
- User-Agent derivado da versão do binário do Chrome em tempo de execução, removendo o
  marcador `HeadlessChrome`. É derivado, e não fixo, para não divergir do header
  `Sec-CH-UA` quando o Chrome atualizar
- `screen` e `viewport` coerentes entre si, com a janela cabendo dentro da tela
- `locale` pt-BR e fuso de São Paulo

**Plataformas serverless (Vercel, Cloud Functions) não servem para o bot**: o limite de
execução é menor que uma consulta com rate limit, não há display X nem Mesa, e não há como
instalar pacotes de sistema. O solver, por ser stateless, roda bem nelas.

### A versão do Chrome importa

O `Dockerfile` fixa o Chrome em uma versão exata (`CHROME_VERSION`, via Chrome for Testing),
e isso não é preciosismo: com o Chrome 153 a Receita **rejeita** a consulta, com o 140 aceita,
no mesmo container e com todo o resto idêntico. Uma diferença observável entre as duas é
`navigator.deviceMemory`, que passa a reportar `32` no 153 — valor acima do teto de `8` que a
especificação define e que nenhum navegador comum reporta.

Instalar `google-chrome-stable` sem fixar versão faz o ambiente mudar sozinho a cada rebuild,
com o bot deixando de funcionar sem nenhuma alteração de código. Ao atualizar a versão, rode
uma consulta real antes de promover a imagem.

### Docker

```bash
docker build -t receipt-cpf-bot .
docker run --rm -p 8000:8000 --env-file .env receipt-cpf-bot
```

A imagem já sobe o Xvfb pelo entrypoint e respeita a `$PORT` (o Render a define
automaticamente). O perfil do Chrome pode começar vazio, então **não é necessário disco
persistente**.

O recurso que limita é **CPU**, não memória — o llvmpipe rasteriza no processador. Medições de
uma consulta real dentro do container:

| CPU / RAM | Resultado |
| --- | --- |
| 0,1 / 512 MB | falha: o widget do hCaptcha não carrega a tempo |
| 0,5 / 512 MB | ok, ~38s |
| 1,0 / 2 GB | ok, ~29s |

512 MB bastam; abaixo de meio núcleo, não.

Em plataformas como Render ou Cloud Run, escolha o runtime **Docker**; ambientes de runtime
nativo não permitem instalar Chrome, Xvfb e Mesa. Use `/api/v1/health` como health check path.

## Limites conhecidos

**Não suporta requisições concorrentes.** Todas as sessões usam o mesmo diretório de perfil
(`.chrome-profile`), e o Chrome permite um único processo por perfil: uma segunda requisição
simultânea falha com `ProcessSingleton`. Antes de expor a API a tráfego real é preciso
serializar as consultas ou usar um perfil por sessão.

O CDN de imagens do hCaptcha aplica rate limit (HTTP 429) a consultas em sequência rápida. O
solver recua com backoff exponencial (5s a 120s, até 6 tentativas) e só então desiste, com
`CaptchaRateLimited`.

## Testes

```bash
uv run pytest
uv run ruff check .
```

Os testes não acessam a rede: o navegador, o solver e a Receita são substituídos por fakes.
