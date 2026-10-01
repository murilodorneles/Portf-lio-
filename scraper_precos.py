import csv
import json
import time
import random
import argparse
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

CABECALHO = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9",
}


def pega_preco(html):
    soup = BeautifulSoup(html, "html.parser")
    meta = soup.find("meta", {"itemprop": "price"})
    if meta and meta.get("content"):
        try:
            return float(meta["content"])
        except ValueError:
            pass
    el = soup.select_one(".andes-money-amount__fraction")
    if el:
        txt = el.get_text(strip=True).replace(".", "").replace(",", ".")
        try:
            return float(txt)
        except ValueError:
            pass
    return None


def pega_titulo(html):
    soup = BeautifulSoup(html, "html.parser")
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)
    return soup.title.get_text(strip=True) if soup.title else "?"


def consulta(url, timeout=20):
    try:
        r = requests.get(url, headers=CABECALHO, timeout=timeout)
    except requests.RequestException as e:
        return {"url": url, "erro": str(e)[:80]}

    if r.status_code != 200:
        return {"url": url, "erro": f"HTTP {r.status_code}"}

    return {
        "url": url,
        "titulo": pega_titulo(r.text),
        "preco": pega_preco(r.text),
        "quando": datetime.now().isoformat(timespec="seconds"),
    }


def le_urls(caminho):
    linhas = Path(caminho).read_text(encoding="utf-8").splitlines()
    return [l.strip() for l in linhas if l.strip() and not l.startswith("#")]


def salva_csv(itens, caminho):
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["url", "titulo", "preco", "quando", "erro"])
        w.writeheader()
        for it in itens:
            w.writerow({k: it.get(k, "") for k in w.fieldnames})


def salva_json(itens, caminho):
    Path(caminho).write_text(
        json.dumps(itens, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def compara(antigos, novos):
    p = Path(antigos)
    if not p.exists():
        return []
    velho = {x["url"]: x.get("preco") for x in json.loads(p.read_text("utf-8"))}
    mudou = []
    for it in novos:
        antes = velho.get(it["url"])
        agora = it.get("preco")
        if antes and agora and antes != agora:
            pct = (agora - antes) / antes * 100
            mudou.append({**it, "antes": antes, "pct": round(pct, 2)})
    return mudou


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--input", default="urls.txt")
    ap.add_argument("-o", "--output", default="precos.csv")
    ap.add_argument("--json", default="precos.json")
    ap.add_argument("--historico", default="historico.json")
    ap.add_argument("--delay", type=float, default=2.0)
    args = ap.parse_args()

    urls = le_urls(args.input)
    print(f"{len(urls)} url(s)\n")

    itens = []
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] {url}")
        it = consulta(url)
        if it.get("preco"):
            print(f"    {it['titulo'][:60]}")
            print(f"    R$ {it['preco']:.2f}")
        else:
            print(f"    erro: {it.get('erro', 'sem preco')}")
        itens.append(it)
        if i < len(urls):
            time.sleep(args.delay + random.uniform(0, 1))

    salva_csv(itens, args.output)
    salva_json(itens, args.json)
    print(f"\nsalvo em {args.output}")

    mudou = compara(args.historico, itens)
    if mudou:
        print(f"\n{len(mudou)} mudanca(s):")
        for m in mudou:
            seta = "↓" if m["pct"] < 0 else "↑"
            print(f"  {seta} {m['pct']:+.1f}%  {m['titulo'][:50]}")
            print(f"     R$ {m['antes']:.2f} -> R$ {m['preco']:.2f}")


if __name__ == "__main__":
    main()