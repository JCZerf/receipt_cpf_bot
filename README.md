# receipt_cpf_bot

Consulta a situação cadastral de um CPF no site público da Receita Federal, resolvendo o
hCaptcha da página automaticamente. Expõe a consulta por CLI e por API HTTP.

## Arquitetura

Três camadas, com dependência em uma direção só: `api` → `bot` → `core`.

```
api/     camada externa de comunicação (HTTP)
  main.py      aplicação FastAPI
  router.py    agregação das rotas
  routes/      cpf, health
  schemas.py   contrato HTTP (Pydantic)
  config.py    PROJECT_NAME, API_V1_STR

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
  "success": true,
  "message": "query completed",
  "record": {
    "cpf": "123.456.789-01",
    "name": "FULANO DE TAL",
    "birth_date": "07/08/1978",
    "status": "REGULAR",
    "registration_date": "13/11/1996",
    "check_digit": "00",
    "issued_at": "20:12:38 do dia 20/09/2026 (hora e data de Brasília).",
    "control_code": "7E48.F960.CBDF.90C2"
  }
}
```

Documentação interativa em `/docs`. Health check em `/api/v1/health`.

Quando o captcha não é resolvido dentro do limite de rodadas, a API responde `503`.

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
execução é menor que uma consulta com rate limit, não há display X nem Mesa, e o perfil do
Chrome não sobrevive entre invocações. O solver, por ser stateless, roda bem nelas.

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
