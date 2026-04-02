"""
Monitor de Editais - INBIO/UFU
Verifica diariamente https://www.inbio.ufu.br/editais e notifica via
Telegram Bot se houver novos editais além do último estado salvo.
"""

import json
import os
import smtplib
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()  # Carrega variáveis do arquivo .env (ignorado pelo git)

# ─── Configuração ────────────────────────────────────────────────────────────

URL_EDITAIS = "https://www.inbio.ufu.br/editais"
STATE_FILE = Path(__file__).parent / "editais_state.json"

# ── Telegram (recomendado — sem senha!) ──────────────────────────────────────
# Veja o README para saber como obter esses dois valores em 2 minutos.
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")    # token do bot, ex: 123456:ABC-xyz
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")  # seu chat ID numérico

# ── Email via Outlook (opcional) ─────────────────────────────────────────────
EMAIL_REMETENTE = os.environ.get("MONITOR_EMAIL_FROM")
EMAIL_SENHA = os.environ.get("MONITOR_EMAIL_PASSWORD")
EMAIL_DESTINATARIO = os.environ.get("MONITOR_EMAIL_TO")

SMTP_HOST = "smtp-mail.outlook.com"
SMTP_PORT = 587

# ─── Scraping ─────────────────────────────────────────────────────────────────

def buscar_editais():
    """Raspa todas as páginas de editais e retorna lista de dicts com título, data e link."""
    editais = []
    page = 0

    while True:
        params = {"page": page} if page > 0 else {}
        try:
            resp = requests.get(URL_EDITAIS, params=params, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"[ERRO] Falha ao acessar página {page}: {e}")
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        rows = soup.select("table tr, .views-row, article")

        # Tenta encontrar linhas com data no formato dd/mm/yyyy
        encontrados_nesta_pagina = []
        for tag in soup.find_all(string=True):
            text = tag.strip()
            # Detecta padrões de data como "06/03/2026 - 12:00"
            if len(text) >= 10 and text[2] == "/" and text[5] == "/" and text[8:12].isdigit():
                data_str = text[:10]  # "dd/mm/yyyy"
                # Tenta pegar o título mais próximo
                parent = tag.parent
                titulo = ""
                link = ""
                # Sobe na árvore em busca de um link ou título
                for _ in range(6):
                    if parent is None:
                        break
                    a_tag = parent.find("a", href=True)
                    if a_tag:
                        titulo = a_tag.get_text(strip=True)
                        href = a_tag["href"]
                        link = href if href.startswith("http") else f"https://www.inbio.ufu.br{href}"
                        break
                    parent = parent.parent

                try:
                    data = datetime.strptime(data_str, "%d/%m/%Y")
                except ValueError:
                    continue

                encontrados_nesta_pagina.append({
                    "titulo": titulo,
                    "data": data_str,
                    "data_obj": data,
                    "link": link,
                })

        if not encontrados_nesta_pagina:
            break

        editais.extend(encontrados_nesta_pagina)

        # Verifica se há próxima página
        proximo = soup.select_one('a[title="Ir para a próxima página"], .pager__item--next a')
        if not proximo:
            break
        page += 1

    # Remove duplicatas por (data, titulo)
    vistos = set()
    unicos = []
    for e in editais:
        chave = (e["data"], e["titulo"])
        if chave not in vistos:
            vistos.add(chave)
            unicos.append(e)

    return sorted(unicos, key=lambda x: x["data_obj"], reverse=True)


# ─── Estado persistente ───────────────────────────────────────────────────────

def carregar_estado():
    if STATE_FILE.exists():
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # Estado inicial padrão
    return {
        "ultima_data_conhecida": "06/03/2026",
        "editais_vistos": []
    }


def salvar_estado(estado):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=2)


# ─── Telegram ────────────────────────────────────────────────────────────────

def enviar_telegram(novos_editais):
    """Envia mensagem via Telegram Bot. Não precisa de senha de email!"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("[AVISO] Telegram não configurado. Configure TELEGRAM_TOKEN e TELEGRAM_CHAT_ID.")
        return False

    linhas = []
    for e in novos_editais:
        titulo = e["titulo"] or "(sem título)"
        link = e["link"]
        if link:
            linhas.append(f"📄 [{titulo}]({link}) — {e['data']}")
        else:
            linhas.append(f"📄 {titulo} — {e['data']}")

    texto = (
        f"🔔 *Novo(s) edital(is) publicado(s) no INBIO/UFU!*\n\n"
        + "\n".join(linhas)
        + f"\n\n🔗 [Ver todos os editais]({URL_EDITAIS})"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": texto,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False,
        }, timeout=15)
        resp.raise_for_status()
        print(f"[OK] Mensagem Telegram enviada!")
        return True
    except requests.RequestException as e:
        print(f"[ERRO] Falha ao enviar Telegram: {e}")
        return False


# ─── Email ────────────────────────────────────────────────────────────────────

def enviar_email(novos_editais):
    if not EMAIL_REMETENTE or not EMAIL_SENHA or not EMAIL_DESTINATARIO:
        return False

    assunto = f"[INBIO/UFU] {len(novos_editais)} novo(s) edital(is) publicado(s)!"

    linhas_html = ""
    for e in novos_editais:
        link_html = f'<a href="{e["link"]}">{e["titulo"] or "(sem título)"}</a>' if e["link"] else (e["titulo"] or "(sem título)")
        linhas_html += f"<li><strong>{e['data']}</strong> — {link_html}</li>\n"

    corpo_html = f"""
    <html><body>
    <h2>Novos editais publicados em INBIO/UFU</h2>
    <ul>
    {linhas_html}
    </ul>
    <p>Acesse: <a href="{URL_EDITAIS}">{URL_EDITAIS}</a></p>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto
    msg["From"] = EMAIL_REMETENTE
    msg["To"] = EMAIL_DESTINATARIO
    msg.attach(MIMEText(corpo_html, "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(EMAIL_REMETENTE, EMAIL_SENHA)
            server.sendmail(EMAIL_REMETENTE, EMAIL_DESTINATARIO, msg.as_string())
        print(f"[OK] Email enviado para {EMAIL_DESTINATARIO}")
        return True
    except smtplib.SMTPException as e:
        print(f"[ERRO] Falha ao enviar email: {e}")
        return False


def notificar(novos_editais):
    """Tenta Telegram primeiro; email como fallback se configurado."""
    enviado = enviar_telegram(novos_editais)
    if not enviado:
        enviar_email(novos_editais)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Verificando editais em {URL_EDITAIS} ...")

    estado = carregar_estado()
    ultima_data = datetime.strptime(estado["ultima_data_conhecida"], "%d/%m/%Y")
    editais_vistos = set(estado.get("editais_vistos", []))

    todos_editais = buscar_editais()
    print(f"[INFO] {len(todos_editais)} edital(is) encontrado(s) no site.")

    novos = []
    for e in todos_editais:
        chave = f"{e['data']}|{e['titulo']}"
        if e["data_obj"] > ultima_data and chave not in editais_vistos:
            novos.append(e)

    if novos:
        print(f"[NOVIDADE] {len(novos)} novo(s) edital(is) encontrado(s)!")
        for e in novos:
            print(f"  - {e['data']} | {e['titulo']} | {e['link']}")
        notificar(novos)

        # Atualiza estado
        maior_data = max(novos, key=lambda x: x["data_obj"])
        if maior_data["data_obj"] > ultima_data:
            estado["ultima_data_conhecida"] = maior_data["data"]
        for e in novos:
            editais_vistos.add(f"{e['data']}|{e['titulo']}")
        estado["editais_vistos"] = list(editais_vistos)
        salvar_estado(estado)
    else:
        print("[INFO] Nenhum edital novo encontrado.")


if __name__ == "__main__":
    main()
