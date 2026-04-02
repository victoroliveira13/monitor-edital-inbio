# 📋 Monitor de Editais — INBIO/UFU

> Monitoramento automático de editais publicados em [inbio.ufu.br/editais](https://www.inbio.ufu.br/editais) com notificação instantânea via **Telegram**.

[![GitHub Actions](https://img.shields.io/badge/Automatizado%20com-GitHub%20Actions-2088FF?logo=github-actions&logoColor=white)](https://github.com/features/actions)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Licença](https://img.shields.io/badge/Licen%C3%A7a-MIT-green)](LICENSE)

---

## ✨ Como funciona

O script roda automaticamente **todo dia às 08h (horário de Brasília)** via GitHub Actions (100% gratuito). Ele:

1. Acessa a página de editais do INBIO/UFU
2. Compara com o último estado salvo
3. Se houver editais novos, envia uma mensagem no seu **Telegram** com título, data e link

Nenhum servidor pago. Nenhuma configuração de email. Basta ter uma conta no GitHub e no Telegram.

---

## 📁 Estrutura do projeto

| Arquivo | Descrição |
|---|---|
| `monitor.py` | Script principal de scraping e notificação |
| `requirements.txt` | Dependências Python |
| `editais_state.json` | Estado persistente — salvo automaticamente a cada execução |
| `.github/workflows/monitor.yml` | Workflow do GitHub Actions (agendamento diário) |

---

## 🚀 Como usar

### Passo 1 — Criar o Telegram Bot (2 minutos)

1. Abra o Telegram e pesquise por **@BotFather**
2. Envie `/newbot` e siga as instruções
3. Anote o **token** gerado: `7123456789:AAHxxxxxxxxxxxxxxxxxxxxxx`

#### Obter seu Chat ID

1. Envie qualquer mensagem para o bot que você criou
2. Acesse no navegador (troque `SEU_TOKEN`):
   ```
   https://api.telegram.org/botSEU_TOKEN/getUpdates
   ```
3. No JSON retornado, procure `"chat":{"id":` — esse número é o seu **Chat ID**

---

### Passo 2 — Criar repositório no GitHub

1. Acesse [github.com](https://github.com) e crie uma conta gratuita (se não tiver)
2. Clique em **New repository**
3. Nome sugerido: `monitor-editais-inbio`
4. Marque como **Private** (recomendado para proteger seus secrets)
5. Clique em **Create repository**

---

### Passo 3 — Enviar os arquivos para o GitHub

**Via upload pelo navegador:**

No repositório criado, clique em **"uploading an existing file"** e faça upload de:
- `monitor.py`
- `editais_state.json`
- `requirements.txt`

Para o workflow, crie a pasta `.github/workflows/` e faça upload de `monitor.yml`.

**Via Git (se tiver instalado):**

```bash
git init
git add .
git commit -m "feat: monitor de editais INBIO/UFU"
git remote add origin https://github.com/SEU_USUARIO/monitor-editais-inbio.git
git push -u origin main
```

---

### Passo 4 — Configurar os secrets do Telegram

1. No repositório, vá em **Settings → Secrets and variables → Actions**
2. Clique em **New repository secret** e adicione os dois abaixo:

| Nome do Secret | Valor |
|---|---|
| `TELEGRAM_TOKEN` | Token do bot (ex: `7123456789:AAHxxx...`) |
| `TELEGRAM_CHAT_ID` | Seu Chat ID numérico (ex: `123456789`) |

> 🔒 Os secrets ficam criptografados no GitHub — ninguém consegue ver o valor, nem você depois de salvo.

---

### Passo 5 — Testar manualmente

1. No repositório, clique em **Actions**
2. Clique no workflow **"Monitor Editais INBIO/UFU"**
3. Clique em **Run workflow → Run workflow**
4. Aguarde ~30 segundos e verifique se chegou mensagem no Telegram ✅

---

## ⏰ Agendamento automático

O workflow está configurado para rodar **todo dia às 08:00 (horário de Brasília)**. Nenhuma configuração extra necessária após o setup.

Para alterar o horário, edite a linha `cron` em `.github/workflows/monitor.yml`:

```yaml
- cron: "0 11 * * *"   # 11:00 UTC = 08:00 Brasília
```

Use [crontab.guru](https://crontab.guru/) para montar outros horários.

---

## 📬 Notificações opcionais por email

O script também suporta envio via email (Outlook/SMTP) como fallback. Configure os seguintes secrets se quiser usar:

| Secret | Descrição |
|---|---|
| `MONITOR_EMAIL_FROM` | Endereço de email remetente |
| `MONITOR_EMAIL_PASSWORD` | Senha do email remetente |
| `MONITOR_EMAIL_TO` | Endereço de email destinatário |

---

## 🛠️ Execução local

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
set TELEGRAM_TOKEN=seu_token
set TELEGRAM_CHAT_ID=seu_chat_id

# Rodar o script
python monitor.py
```

---

## 📄 Licença

Este projeto é livre para uso e adaptação. Fique à vontade para abrir issues ou pull requests.
