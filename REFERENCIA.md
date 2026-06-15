# Referência — Automação PROJUDI-BA

---

## Estrutura do projeto

```
Automações/
├── orquestrador.py              → Ponto de entrada — chama tudo na ordem certa
├── config.py                    → Configurações: senha de peticionamento, de/para de documentos, credenciais Paycon
├── REFERENCIA.md                → Este arquivo
│
├── paycon/
│   ├── __init__.py
│   └── extracao_elaw.py         → Conecta via API ao Odoo/eLaw e exporta todas as tarefas para Excel
│
├── projudi_ba/
│   ├── __init__.py
│   ├── regra_captcha.py         → Login no PROJUDI com captcha de áudio (Whisper)
│   ├── busca_processo.py        → Busca cada processo no PROJUDI e resolve captcha da busca
│   ├── peticionamento.py        → (Em desenvolvimento) Envia petição principal e anexos
│   └── download_comprovante.py  → (Em desenvolvimento) Baixa comprovante e cópia integral
│
└── temp/
    ├── audios/                  → Gravações de áudio dos captchas
    ├── exportacoes/             → Planilhas Excel geradas pelo eLaw
    └── relatorios/              → PDFs de falhas gerados automaticamente
```

---

## O que cada arquivo faz

### `orquestrador.py`
Arquivo principal. Quando rodado, executa todo o fluxo na ordem:
1. Extrai tarefas do eLaw → gera Excel
2. Lê a coluna Processo do Excel
3. Faz login no PROJUDI
4. Para cada processo: busca, resolve captcha, verifica resultado
5. Gera relatório PDF de falhas ao final

> **Comportamento atual:** ao encontrar o primeiro processo com botão **Peticionar** visível, o loop é interrompido (`break`) — o robô ainda não continua para peticionar nem para os processos seguintes. Isso mudará quando `peticionamento.py` e `download_comprovante.py` forem implementados.

**Como rodar:**
```powershell
.venv\Scripts\activate
python orquestrador.py
```

---

### `config.py`
Centraliza todas as configurações sensíveis e configuráveis:
- `PAYCON_EMAIL` / `PAYCON_SENHA` — credenciais do sistema eLaw
- `SENHA_PETICIONAMENTO` — senha para protocolar no PROJUDI
- `TIPOS_DOCUMENTO` — de/para entre os nomes de documentos do Odoo e os nomes no PROJUDI

---

### `paycon/extracao_elaw.py`
Conecta diretamente à API do Odoo (sem abrir navegador) e baixa todos os registros da tela **eLaw Tarefa**. Salva em Excel com as colunas: Created on, ID eLaw, Tarefa, Status eLaw, Pasta, Processo, Qtd. Cadastros, Responsável, Setor Responsável, Grupo de Fase, Prazo.

---

### `projudi_ba/regra_captcha.py`
Responsável pelo login no PROJUDI. Faz:
1. Fecha o Edge automaticamente
2. Abre o Edge com o perfil real do usuário (credenciais salvas)
3. Acessa o PROJUDI e clica em Entrar
4. Detecta o captcha de áudio
5. Grava o áudio do sistema, transcreve com Whisper e digita os números
6. Seleciona a OAB e navega até "Buscar Qualquer Processo"
7. Retorna o contexto e página para os próximos módulos

---

### `projudi_ba/busca_processo.py`
Recebe o número do processo e:
1. Digita no campo de busca (navegando por 3 camadas de frames: `mainFrame → userMainFrame → iframe do captcha`)
2. Clica em Submeter
3. Resolve o captcha de áudio se aparecer
4. Verifica se o botão **Peticionar** está visível
5. Se sim → retorna `True` (processo encontrado)
6. Se não → volta para a busca com `voltar_para_busca()` e retorna `False`

> **Atenção:** o site do PROJUDI usa frames aninhados. Qualquer alteração no layout do site pode quebrar os seletores por XPath.

---

### `projudi_ba/peticionamento.py`
*(Em desenvolvimento — ainda não implementado)* Vai enviar a petição principal, selecionar o tipo de documento, enviar anexos, digitar a senha de peticionamento e confirmar o protocolo.

---

### `projudi_ba/download_comprovante.py`
*(Em desenvolvimento — ainda não implementado)* Vai baixar o comprovante do protocolo e a cópia integral do processo.

---

### `temp/audios/`
Armazena as gravações `.wav` dos captchas (login e busca). Sobrescritos a cada execução.

### `temp/exportacoes/`
Armazena os arquivos Excel gerados pelo eLaw. Nome com timestamp: `elaw_tarefas_YYYYMMDD_HHMMSS.xlsx`.

### `temp/relatorios/`
Armazena os PDFs de falhas gerados automaticamente. Nome com timestamp: `relatorio_falhas_YYYYMMDD_HHMMSS.pdf`. Contém: número do processo e motivo da falha (sem captcha, sem botão Peticionar, erro inesperado).

---

## Linguagem e ambiente

| Item | Valor |
|------|-------|
| Linguagem | Python 3.14 |
| Ambiente virtual | `.venv` (pasta `Automações`) |
| Navegador | Microsoft Edge (perfil real do usuário) |

## Bibliotecas instaladas

| Biblioteca | Para que serve |
|-----------|----------------|
| `playwright` | Controla o navegador automaticamente |
| `playwright-stealth` | Esconde que é automação (anti-bot) |
| `pyaudiowpatch` | Grava o áudio do sistema (loopback WASAPI) |
| `openai-whisper` | Transcreve o áudio do captcha para texto |
| `numpy` | Dependência do Whisper |
| `ffmpeg` | Processa o áudio antes do Whisper |
| `requests` | Comunicação com a API do Odoo |
| `openpyxl` | Geração e leitura de arquivos Excel |
| `reportlab` | Geração de relatórios em PDF |

---

## Camuflagem do robô (anti-detecção)

| Mecanismo | O que faz |
|-----------|-----------|
| `playwright-stealth` | Modifica `navigator.webdriver`, fingerprints de canvas e outros sinais que denunciam automação |
| `--disable-blink-features=AutomationControlled` | Remove o flag do Edge que indica controle por script |
| Perfil real do Edge | Usa histórico, cookies e senhas salvas — parece um usuário humano |

---

## Guia de instalação para novo usuário

### 1. Instalar Python
Baixe em https://www.python.org/downloads/ — marque **"Add Python to PATH"** durante a instalação.

### 2. Instalar FFmpeg
```powershell
winget install "FFmpeg (Essentials Build)"
```
Feche e reabra o terminal após instalar.

### 3. Criar ambiente virtual e instalar dependências
```powershell
cd "CAMINHO\PARA\A\PASTA\Automações"
python -m venv .venv
.venv\Scripts\activate
pip install playwright playwright-stealth pyaudiowpatch openai-whisper numpy requests openpyxl reportlab
python -m playwright install
```

### 4. Ajustar o caminho do perfil do Edge
No arquivo `projudi_ba\regra_captcha.py`, troque o nome do usuário Windows:
```python
user_data_dir=r"C:\Users\SEU_USUARIO\AppData\Local\Microsoft\Edge\User Data",
```
Para descobrir seu usuário: `echo $env:USERNAME`

### 5. Ajustar credenciais no config.py
Preencha `PAYCON_EMAIL` e `PAYCON_SENHA` com as credenciais do sistema eLaw.

### 6. Salvar credenciais do PROJUDI no Edge
Acesse o PROJUDI manualmente no Edge, faça login e salve a senha quando solicitado.

---

## Erros comuns e soluções

| Erro | Causa | Solução |
|------|-------|---------|
| `Abrindo em uma sessão existente` | Edge estava aberto | `taskkill /IM msedge.exe /F` |
| `ModuleNotFoundError` | .venv não ativado | `.venv\Scripts\activate` |
| `ffmpeg not found` | FFmpeg não instalado | `winget install "FFmpeg (Essentials Build)"` |
| `ERR_CONNECTION_TIMED_OUT` | Site do PROJUDI fora do ar | Aguardar e tentar novamente |
| Whisper transcreve vazio | Áudio não capturado | Verificar volume do sistema e dispositivo de saída padrão |
| `TargetClosedError` | Navegador fechado manualmente | Normal, não é problema |
