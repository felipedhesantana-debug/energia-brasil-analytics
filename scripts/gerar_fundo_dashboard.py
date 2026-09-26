"""
Gera os fundos (layout) das 3 páginas do dashboard: faixa azul, cards brancos, tiles amarelos,
rótulos, ícones e o anel (donut) do 4º indicador. Os números e gráficos vêm do Tableau.

Uso: python scripts/gerar_fundo_dashboard.py
"""
import sys
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import layout_dashboard as L  # noqa: E402

BASE = Path(__file__).resolve().parents[1]
S = 2  # desenha em 2x e reduz (bordas suaves)
FUNDO = (240, 242, 246)
CINZA = (120, 128, 145)


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def fonte(tam, negrito=False):
    nome = "Carlito-Bold.ttf" if negrito else "Carlito-Regular.ttf"
    for pasta in ["/usr/share/fonts/truetype/crosextra/", "/usr/share/fonts/truetype/carlito/"]:
        if Path(pasta + nome).exists():
            return ImageFont.truetype(pasta + nome, tam * S)
    return ImageFont.truetype("DejaVuSans-Bold.ttf" if negrito else "DejaVuSans.ttf", tam * S)


def r(box):
    x, y, w, h = box
    return [x * S, y * S, (x + w) * S, (y + h) * S]


def percentuais():
    """Valores dos anéis (donuts), calculados a partir da base exportada da camada gold."""
    e = pd.read_csv(BASE / "tableau" / "dados" / "mart_energia_dashboard.csv", parse_dates=["data"])
    m = pd.read_csv(BASE / "tableau" / "dados" / "mart_matriz_perfil.csv")
    ano = e["ano"].max()
    se = e[(e["subsistema_id"] == "SE") & (e["ano"] == ano)]
    mm = m[m["ano"] == m["ano"].max()]
    tot = mm["energia_twh"].sum()
    return {
        "pct_horas_zero": se["hora_cmo_zero"].mean(),
        "pct_eol_sol": mm[mm["fonte"].isin(["2. Solar", "4. Eólica"])]["energia_twh"].sum() / tot,
        "pct_ear_ano": se["ear_pct"].mean() / 100,
    }


def desenhar(pagina, pct):
    c = L.CONTEUDO[pagina]
    img = Image.new("RGB", (L.W * S, L.H * S), FUNDO)
    d = ImageDraw.Draw(img)

    # faixa azul em degradê + linha amarela
    alt = 205
    a1, a2 = rgb(L.AZUL_1), rgb(L.AZUL_2)
    for yy in range(alt * S):
        t = yy / (alt * S)
        d.line([(0, yy), (L.W * S, yy)], fill=tuple(int(a1[i] + (a2[i] - a1[i]) * t) for i in range(3)))
    d.rectangle([0, alt * S, L.W * S, (alt + 4) * S], fill=rgb(L.AMARELO))

    # sombras
    sombra = Image.new("L", img.size, 0)
    ds = ImageDraw.Draw(sombra)
    for box in L.KPIS + [L.PRINCIPAL, L.LATERAL] + L.TILES:
        x0, y0, x1, y1 = r(box)
        ds.rounded_rectangle([x0, y0 + 6 * S, x1, y1 + 6 * S], 14 * S, fill=60)
    sombra = sombra.filter(ImageFilter.GaussianBlur(10 * S))
    img = Image.composite(Image.new("RGB", img.size, (170, 176, 190)), img, sombra)
    d = ImageDraw.Draw(img)

    for box in L.KPIS + [L.PRINCIPAL, L.LATERAL]:
        d.rounded_rectangle(r(box), 14 * S, fill=(255, 255, 255))
    for box, cor in zip(L.TILES, L.TILE_CORES):
        d.rounded_rectangle(r(box), 14 * S, fill=rgb(cor))

    # logo + título
    x, y = 60, 34
    d.rounded_rectangle([x * S, y * S, (x + 40) * S, (y + 40) * S], 9 * S, fill=(255, 255, 255))
    raio = [(23, 5), (11, 22), (19, 22), (15, 35), (29, 17), (21, 17), (25, 5)]  # raio (energia)
    d.polygon([((x + px) * S, (y + py) * S) for px, py in raio], fill=rgb(L.AMARELO))
    d.text(((x + 54) * S, (y - 2) * S), L.TITULO, font=fonte(24, True), fill="white")
    d.text(((x + 54) * S, (y + 26) * S), c["subtitulo"], font=fonte(14), fill=(200, 212, 240))

    # aba ativa (contorno); os textos das abas são botões do Tableau
    ax, ay, aw, ah = L.ABAS[pagina]
    d.rounded_rectangle([ax * S, ay * S, (ax + aw) * S, (ay + ah) * S], 6 * S, outline="white", width=2 * S)

    def centro(txt, box, dy, f, cor):
        bx, by, bw, _ = box
        tw = d.textlength(txt, font=f) / S
        d.text(((bx + (bw - tw) / 2) * S, (by + dy) * S), txt, font=f, fill=cor)

    for i, (rot, _) in enumerate(c["kpis"]):
        b = L.KPIS[i] if i < 3 else (L.KPIS[i][0], L.KPIS[i][1], L.KPIS[i][2] - 100, L.KPIS[i][3])
        centro(rot, b, 16, fonte(13), CINZA)
    centro(c["principal"][0], L.PRINCIPAL, 18, fonte(17), (70, 78, 95))
    centro(c["lateral"][0], L.LATERAL, 18, fonte(17), (70, 78, 95))
    for (rot, _), box in zip(c["tiles"], L.TILES):
        centro(rot, box, 96, fonte(14, True), (255, 255, 255))

    # ícones dos tiles
    for box, simb in zip(L.TILES, c["icones"]):
        bx, by, _, _ = box
        cx, cy, rr = bx + 34, by + 36, 18
        d.ellipse([(cx - rr) * S, (cy - rr) * S, (cx + rr) * S, (cy + rr) * S], outline="white", width=2 * S)
        f = ImageFont.truetype("DejaVuSans-Bold.ttf", 16 * S)
        tw = d.textlength(simb, font=f) / S
        d.text(((cx - tw / 2) * S, (cy - 11) * S), simb, font=f, fill="white")

    # donut do 4º KPI
    cx, cy = L.DONUT["centro"]
    rr, esp = L.DONUT["raio"], 11
    caixa = [(cx - rr) * S, (cy - rr) * S, (cx + rr) * S, (cy + rr) * S]
    d.ellipse(caixa, outline=(236, 238, 242), width=esp * S)
    d.arc(caixa, -90, -90 + 360 * pct[c["donut"]], fill=rgb(L.AMARELO), width=esp * S)

    # legendas (cores = paleta padrão do Tableau, na ordem alfabética dos valores)
    def legenda(itens, box):
        bx, by, bw, bh = box
        f = fonte(13)
        larguras = [22 + d.textlength(t, font=f) / S + 22 for t, _ in itens]
        x0 = bx + (bw - sum(larguras)) / 2
        y0 = by + bh - 34
        for (t, cor), lw in zip(itens, larguras):
            d.rounded_rectangle([x0 * S, (y0 + 3) * S, (x0 + 14) * S, (y0 + 17) * S], 3 * S, fill=rgb(cor))
            d.text(((x0 + 20) * S, y0 * S), t, font=f, fill=CINZA)
            x0 += lw

    if "leg_principal" in c:
        legenda(c["leg_principal"], L.PRINCIPAL)
    if "leg_lateral" in c:
        legenda(c["leg_lateral"], L.LATERAL)

    d.text((60 * S, 872 * S), "Fonte: ONS — Operador Nacional do Sistema Elétrico (dados abertos) · Pipeline: Colab + Python → DuckDB → dbt → Tableau",
           font=fonte(11), fill=(140, 146, 160))
    return img.resize((L.W, L.H), Image.LANCZOS)


def main():
    pct = percentuais()
    pasta = BASE / "tableau" / "assets"
    pasta.mkdir(parents=True, exist_ok=True)
    for p in L.PAGINAS:
        destino = pasta / f"fundo_{L.slug(p)}.png"
        desenhar(p, pct).save(destino)
        print("Fundo salvo:", destino.relative_to(BASE))


if __name__ == "__main__":
    main()
