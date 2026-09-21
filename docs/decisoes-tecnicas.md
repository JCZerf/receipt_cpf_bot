# Decisões técnicas

Registro do que foi decidido, por quê, e qual medição sustenta cada decisão. Existe porque
quase nada aqui é óbvio pelo código: várias escolhas parecem arbitrárias até você ver o
experimento que as produziu, e mais de uma hipótese razoável foi testada e descartada.

Toda medição abaixo é de execução real contra o site da Receita Federal, salvo onde indicado.

---

## 1. O que decide se a Receita aceita o token não é headless

**Decisão:** o bot pode rodar headless ou headful, mas exige um display X (Xvfb) quando não
há GPU.

**Contexto:** a suspeita inicial era que o modo headless fosse detectado e o token do hCaptcha
recusado. A mensagem de erro alimenta essa leitura: a Receita responde
`O Anti-Robô não foi preenchido corretamente` **mesmo com o captcha resolvido**, sem dizer o
motivo. O código chegou a documentar isso como limitação do headless.

**O que a medição mostrou:** a variável que decide é o renderizador do WebGL, não o modo.

| Modo | Renderizador | Resultado |
| --- | --- | --- |
| headless, GPU disponível | NVIDIA (ANGLE, OpenGL 4.5) | aceito |
| headless, sem display X | SwiftShader | **rejeitado** |
| headful sob Xvfb, sem GPU | SwiftShader | **rejeitado** |
| headful sob Xvfb + Mesa | llvmpipe | aceito |
| headless sob Xvfb + Mesa | llvmpipe | aceito |

O SwiftShader é o renderizador de software embutido no Chrome. Ele praticamente não aparece
em máquina de usuário real, então funciona como assinatura de automação. Já o `llvmpipe`, do
Mesa, é o que uma VM Linux comum sem GPU reporta de verdade — e passa.

**Consequência:** sem display X não há como alcançar o llvmpipe. O Chrome cai em SwiftShader
com ou sem as flags de GL, o que foi verificado removendo `DISPLAY` do ambiente. Por isso o
container roda Xvfb (`docker-entrypoint.sh`) e não apenas `--headless`.

**Hipótese descartada:** "renderização por software é detectada". Falsa. Software puro
(llvmpipe) passa; o que não passa é o SwiftShader especificamente.

---

## 2. As flags de GL valem nos dois modos

**Decisão:** `GL_ARGS` (em `bot/browser/fingerprint.py`) é aplicado tanto em headless quanto
em headful.

**Por quê:** `--ignore-gpu-blocklist` é obrigatório. Sem ele o Chrome recusa o llvmpipe por
blocklist e volta ao SwiftShader — medido: com as flags, `ANGLE (Mesa, llvmpipe ...)`; sem
elas, `ANGLE (Google, ... SwiftShader driver)`, no mesmo Xvfb.

Antes, as flags só eram aplicadas em headless. Um container rodando headful sob Xvfb caía em
SwiftShader silenciosamente, que é exatamente o cenário rejeitado.

---

## 3. A versão do Chrome é fixada no Dockerfile

**Decisão:** `CHROME_VERSION` fixa uma build exata, obtida do Chrome for Testing, em vez de
instalar `google-chrome-stable`.

**Por quê:** com **Chrome 153 a consulta é rejeitada; com 140, aceita** — mesmo container,
mesmo llvmpipe, mesmo perfil, todo o resto idêntico. Testado com perfil frio e com perfil
aquecido: os dois falharam no 153.

Uma diferença observável entre as versões: `navigator.deviceMemory` reporta `32` no 153 e `8`
no 140. A especificação limita esse valor a 8, e nenhum navegador comum reporta 32. Não está
provado que esse é o sinal lido pela Receita — o 153 muda mais coisas —, mas a **versão** está
isolada como causa.

**Consequência operacional:** instalar a stable do dia faz o ambiente mudar sozinho a cada
rebuild, e o bot pararia de funcionar sem nenhuma alteração de código. Ao atualizar a versão,
rode uma consulta real antes de promover a imagem.

**Hipótese descartada:** "o Patchright não suporta Chrome novo". Falsa — o Chromium que o
Patchright empacota é o `153.0.8010.12`. Quem estava fora da faixa era a máquina de
desenvolvimento, com Chrome 140.

---

## 4. O User-Agent é derivado, não fixo

**Decisão:** o UA é montado em tempo de execução a partir da versão do binário
(`chrome_user_agent()`), removendo o marcador `HeadlessChrome`.

**Por quê:** em headless o Chrome anuncia `HeadlessChrome/140...` no UA. Medido: headless com
GPU real **mas com o UA padrão** foi rejeitado; com o UA corrigido, aceito.

Fixar a string no código resolveria hoje e quebraria depois: o header `Sec-CH-UA` é gerado
pelo próprio Chrome e acompanha a versão real. Num update, o UA diria 140 e o `Sec-CH-UA`
diria 141 — incoerência que entrega mais do que o marcador original.

Verificado também que o `Sec-CH-UA` **não** vaza o modo headless: em headless ele já reporta
`"Google Chrome";v="140"`, igual ao headful.

---

## 5. Resolução 1280x720

**Decisão:** `SCREEN_WIDTH`/`SCREEN_HEIGHT` valem 1280x720, e o Xvfb do container acompanha.

**Por quê:** o llvmpipe rasteriza na CPU, então área de tela vira tempo de processador
diretamente. Com meio núcleo e 512 MB:

| Resolução | CPU/RAM | Resultado |
| --- | --- | --- |
| 1920x1080 | 0,5 / 512 MB | falha: timeout esperando o desafio renderizar |
| 1280x720 | 0,5 / 512 MB | sucesso, ~39s |

A Receita aceitou a tela menor. O risco considerado era `screen` menor virar sinal de
fingerprint; não se confirmou.

O `viewport` é derivado da tela descontando a moldura do Chrome, para a janela caber dentro
do monitor. Janela maior que a tela é incoerência que não acontece em uso real.

---

## 6. CPU é o recurso que limita, não memória

**Decisão:** dimensionar por CPU.

**Medições** (consulta real dentro do container, perfil frio):

| CPU / RAM | Resultado |
| --- | --- |
| 0,1 / 512 MB | falha, mesmo elevando os timeouts para 90s (198s até desistir) |
| 0,5 / 512 MB | sucesso, ~39s |
| 1,0 / 1 GB | sucesso, ~29s |
| 2,0 / 2 GB (Cloud Run) | sucesso, ~25s |

As métricas do Render confirmaram do outro lado: pico de **~65% de memória** e **~300% de
CPU** — ou seja, o processo pedia três vezes a CPU disponível e apanhava de throttling.

**Hipótese descartada:** "512 MB não comporta o Chrome". Falsa. A medição de ~450 MB (PSS) foi
feita em container sem limite, onde o Chrome aloca à vontade; sob um cgroup de 512 MB ele se
ajusta e funciona.

**Contraintuitivo, e medido:** renderizar por software custa **mais** memória, não menos —
366 MB com GPU contra 465 MB com llvmpipe, com a página da Receita aberta. Sem GPU os buffers
ficam na RAM do sistema e o llvmpipe compila shaders em tempo de execução.

---

## 7. Chrome, e não outro navegador

**Decisão:** manter o Chrome.

**Por quê:** a intuição era que o Chrome fosse pesado demais para container pequeno. Medido
com a página da Receita aberta:

| Navegador | RAM (PSS) | Disco |
| --- | --- | --- |
| Chrome | 449 MB | 379 MB |
| Firefox | **656 MB** | 275 MB |

O Firefox consome ~45% mais memória. Além disso, o Patchright só instrumenta Chromium de
verdade: no Firefox o `page.evaluate` falhou com erro interno, e o anti-fingerprint que hoje
zera `navigator.webdriver`, plugins e `window.chrome` se perderia.

Também foi descartado o `chromium_headless_shell` (254 MB em disco): sendo headless-only, não
tem janela X e cai em SwiftShader.

Flags de enxugamento de memória (`--renderer-process-limit=1`, `--js-flags=--max-old-space-size`,
`--no-zygote`) foram testadas e **não ajudaram**: 469 MB contra 449 MB, ligeiramente pior. O
piso é o Chrome existir — 223 MB só com uma página em branco.

---

## 8. Backoff para o rate limit do hCaptcha

**Decisão:** ao receber HTTP 429 buscando as imagens do desafio, recuar com backoff
exponencial (5s a 120s, até 6 tentativas) e só então falhar com `CaptchaRateLimited`.

**Por quê:** o CDN de imagens do hCaptcha limita consultas em sequência rápida. O código
anterior tratava a resposta 429 como "imagem quebrada" — porque o corpo não era JPEG — e
reagia **pedindo outro desafio imediatamente**, o que aprofundava o bloqueio. As 20 rodadas
queimavam em ~5 segundos e a consulta falhava.

Depois da correção, o mesmo cenário se resolveu sozinho: quatro esperas (5s, 10s, 20s, 40s)
seguradas até o CDN liberar, e o captcha caiu em duas rodadas.

Rodadas bloqueadas por 429 não consomem o orçamento de `MAX_ROUNDS`, que existe para
tentativas reais de resolver.

**Lição registrada:** o `except Exception: pass` nos laços de espera escondeu esse erro por
horas. Falha de rede disfarçada de falha de conteúdo custa caro para diagnosticar.

---

## 9. Um perfil do Chrome por consulta

**Decisão:** cada consulta cria um perfil descartável em `CHROME_PROFILE_ROOT` e o remove ao
final.

**Por quê:** o Chrome permite um único processo por perfil. Com um diretório fixo, a segunda
consulta simultânea abortava com `ProcessSingleton` — reproduzido: `req1: OK`,
`req2: FALHOU -> Failed to create a ProcessSingleton`.

O `--concurrency=1` do Cloud Run mascarava o problema, já que requisições paralelas vão para
instâncias diferentes. Em qualquer host rodando um container só, ou com `uvicorn --workers 2`,
quebraria — e a mensagem aponta para "corrupção de perfil", não para concorrência.

Perfil frio é suficiente, o que foi confirmado antes de adotar a solução: a consulta no
container com perfil zerado passou. Depois da mudança, três sessões simultâneas terminam no
mesmo tempo de uma (2,7s), ou seja, em paralelo real.

---

## 10. Plataforma de deploy

**Decisão:** Cloud Run, região São Paulo, 2 vCPU, `--concurrency=1`.

**Serverless de função (Vercel, Cloud Functions) foi descartado**, e não por ajuste fino:
não há display X nem Mesa, não há como instalar pacotes de sistema, e o limite de execução é
menor que uma consulta que pegue rate limit. O **solver** de captcha, por ser stateless e
responder em milissegundos, roda bem nessas plataformas — e é onde está.

**Render** funcionaria no plano de 0,5 CPU com a resolução reduzida, mas o de 0,1 CPU (free)
não: falhou mesmo com timeouts de 90s.

O `--concurrency=1` continua fazendo sentido mesmo depois do perfil por sessão: cada consulta
usa CPU de forma intensiva, e dividir uma instância entre duas consultas degrada as duas.

**Hipótese descartada:** "IP de datacenter é recusado pela Receita". Não se confirmou — a
consulta do Cloud Run passou. Vale notar que todas as falhas anteriores em nuvem eram de CPU,
o que mantinha essa dúvida viva sem evidência.

---

## 11. Configuração obrigatória falha na inicialização

**Decisão:** `SOLVER_URL`, `SOLVER_API_KEY` e `API_KEY` não têm valor padrão.

**Por quê:** o padrão anterior de `SOLVER_URL` apontava para `http://127.0.0.1:8001`, um
solver local que não existe em nenhum ambiente real. Faltando a configuração, o processo não
falhava: tentava localhost, tomava connection refused e o sintoma virava erro de rede.

Sem padrão, o processo não sobe e a mensagem diz qual variável falta. No caso da `API_KEY`,
evita também subir uma API de dados pessoais sem autenticação por esquecimento.

---

## 12. Contrato de resposta alinhado aos outros coletores

**Decisão:** responder com o envelope `metadata` → `source_data` → `fields[]`, cada campo com
`name`, `origin` e `value`.

**Por quê:** o mesmo formato do `nfse_bh`, para que quem já consome um coletor leia o outro do
mesmo jeito. A `origin` sai da própria definição do domínio, em `bot/models.py`, onde cada
campo já declara de onde é extraído — o contrato HTTP deriva do domínio em vez de duplicá-lo.

Erros foram mapeados por tipo em vez de um 503 genérico: `404` CPF não consta, `422` dado não
confere, `502` captcha rejeitado ou página não reconhecida, `503` rate limit do hCaptcha.

**Diferença consciente em relação ao `nfse_bh`:** lá o `source_data` carrega `xml_base64`,
porque a NFS-e tem XML assinado como artefato oficial. A Receita devolve só HTML de tela, que
não tem valor probatório equivalente, então incluí-lo inflaria a resposta sem ganho.

---

## Como as validações foram feitas

As conclusões acima vieram de três tipos de teste, e a distinção importa para reproduzi-las:

**Sondas de fingerprint**, baratas e sem custo de solver: sobem o navegador, abrem uma página
em branco e leem os sinais via `page.evaluate` — renderizador WebGL, User-Agent,
`navigator.webdriver`, plugins, `screen`, `deviceMemory`, locale. Foram usadas para comparar
configurações lado a lado antes de gastar uma consulta real.

A comparação headful × headless afinado, por exemplo, mostrou **todos** os sinais idênticos:
`webdriver`, plugins, mimeTypes, `window.chrome`, `permissionsQuery`, timezone, WebGL, screen
e UA. O que provou que a diferença estava no renderizador, não em algum vazamento de
automação.

**Consultas reais** contra a Receita, que são as únicas que respondem se o token é aceito.
Custam crédito do solver e sofrem rate limit se repetidas em sequência, então foram usadas só
para decidir, nunca para explorar.

**Testes automatizados** (99, via `pytest`), que não acessam a rede: navegador, solver e
Receita são substituídos por fakes. Eles cobrem o laço do captcha, o backoff, a normalização
de entrada, o contrato da API, a autenticação e o isolamento dos perfis — mas, por construção,
não conseguem detectar mudança de comportamento da fonte.

**Medição dentro do container**, e não só no host, revelou diferenças que nenhum teste local
pegaria: o pacote `xauth` ausente, o `xvfb-run` falhando silenciosamente como PID 1, e a
versão do Chrome divergente. Vale rodar a consulta real dentro da imagem antes de promovê-la.

---

## Em aberto

- **`except Exception: pass`** nos laços de espera de `bot/browser/hcaptcha.py` engole
  qualquer erro, não só timeout. Foi o que escondeu o 429.
- **`MIN_TARGETS_TO_SUBMIT`**: o log diz "skipping" mas o código submete assim mesmo. Nome e
  comportamento discordam.
- **Sem CI**: os testes e o ruff existem, mas nada os roda automaticamente.
- **Pergunta desconhecida do hCaptcha**: se a fonte rotacionar as categorias, o solver responde
  422 e não há métrica que avise antes do cliente notar.
- **Segredos**: em produção estão no Secret Manager, mas o `.env` local continua em texto puro.
