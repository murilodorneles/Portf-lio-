import os
import re
import time
import argparse
from urllib.parse import urljoin, urlparse
from pathlib import Path

import requests
from bs4 import BeautifulSoup

CABECALHO = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


def acha_pdfs(html, base):
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.lower().endswith(".pdf"):
            links.add(urljoin(base, href))
    return sorted(links)


def nome_seguro(url):
    caminho = urlparse(url).path
    nome = os.path.basename(caminho) or "arquivo.pdf"
    return re.sub(r"[^\w\-_.]", "_", nome)


def baixa(url, destino):
    try:
        r = requests.get(url, headers=CABECALHO, timeout=30, stream=True)
        r.raise_for_status()
        with open(destino, "wb") as f:
            for pedaco in r.iter_content(chunk_size=8192):
                f.write(pedaco)
        return True
    except requests.RequestException as e:
        print(f"    erro: {e}")
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url", help="pagina que tem links de PDF")
    ap.add_argument("-o", "--output", default="pdfs", help="pasta de destino")
    ap.add_argument("--delay", type=float, default=1.0)
    args = ap.parse_args()

    destino = Path(args.output)
    destino.mkdir(parents=True, exist_ok=True)

    print(f"baixando de {args.url}")
    try:
        r = requests.get(args.url, headers=CABECALHO, timeout=20)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"erro: {e}")
        return

    pdfs = acha_pdfs(r.text, args.url)
    print(f"{len(pdfs)} pdf(s) encontrado(s)\n")

    baixados = 0
    for i, url in enumerate(pdfs, 1):
        nome = nome_seguro(url)
        caminho = destino / nome
        print(f"[{i}/{len(pdfs)}] {nome}")
        if baixa(url, caminho):
            baixados += 1
        if i < len(pdfs):
            time.sleep(args.delay)

    print(f"\n{baixados}/{len(pdfs)} baixados em {destino}")


if __name__ == "__main__":
    main()