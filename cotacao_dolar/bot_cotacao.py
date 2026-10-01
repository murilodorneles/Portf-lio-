import os
import time
import logging
from datetime import datetime

import requests
from telegram import Bot
from telegram.error import TelegramError

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("cotacao")

TOKEN = os.getenv("BOT_TOKEN", "")
CHAT_ID = os.getenv("CHAT_ID", "")

INTERVALO = 60 * 60

URL = "https://economia.awesomeapi.com.br/last/USD-BRL,EUR-BRL,BTC-BRL"


def pega_cotacoes():
    try:
        r = requests.get(URL, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        log.warning("falha na requisicao: %s", e)
        return None


def formata(dados):
    linhas = [f"Cotacoes - {datetime.now().strftime('%d/%m %H:%M')}", ""]
    for chave in ("USDBRL", "EURBRL", "BTCBRL"):
        item = dados.get(chave)
        if not item:
            continue
        nome = item["name"]
        valor = float(item["bid"])
        pct = float(item["pchange"])
        seta = "▲" if pct > 0 else ("▼" if pct < 0 else "—")
        linhas.append(f"{nome}: R$ {valor:,.2f}  {seta} {pct:+.2f}%")
    return "\n".join(linhas)


def envia(bot, texto):
    try:
        bot.send_message(chat_id=CHAT_ID, text=texto)
        log.info("enviado")
    except TelegramError as e:
        log.warning("erro telegram: %s", e)


def main():
    if not TOKEN or not CHAT_ID:
        print("Defina BOT_TOKEN e CHAT_ID no ambiente.")
        return

    bot = Bot(token=TOKEN)
    print("Rodando. Ctrl+C pra parar.")

    while True:
        dados = pega_cotacoes()
        if dados:
            texto = formata(dados)
            print(texto)
            envia(bot, texto)
        time.sleep(INTERVALO)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nparado")