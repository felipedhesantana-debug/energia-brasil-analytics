"""
Monta o dashboard final (tableau/energia_dashboard.twbx) a partir de:
  - tableau/energia_base.twbx -> criado no Tableau Public conectando os 2 Excel da camada gold
                                 (guarda as conexões + extrações .hyper, exigidas pelo Tableau Public)
  - scripts/gerar_workbook_tableau.py -> planilhas, campos calculados, painéis e navegação
  - tableau/assets/fundo_*.png -> fundos das 3 páginas

Uso: python scripts/montar_twbx.py
"""
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gerar_workbook_tableau as g  # noqa: E402
import layout_dashboard as L  # noqa: E402

BASE = Path(__file__).resolve().parents[1]
ORIGEM = BASE / "tableau" / "energia_base.twbx"
DESTINO = BASE / "tableau" / "energia_dashboard.twbx"
TABELAS = {"energia": "mart_energia_dashboard", "matriz": "mart_matriz_perfil"}


def main():
    with zipfile.ZipFile(ORIGEM) as z:
        nome_twb = next(n for n in z.namelist() if n.endswith(".twb"))
        twb = z.read(nome_twb).decode("utf-8")
        outros = {n: z.read(n) for n in z.namelist() if n != nome_twb and not n.startswith("Image/")}

    g.SIMPLE_ID = "SheetIdentifierTracking" in twb
    for recurso in ["BasicButtonObject", "BasicButtonObjectTextSupport", "WorksheetBackgroundTransparency"]:
        if f"<{recurso} />" not in twb:
            twb = twb.replace("  </document-format-change-manifest>", f"    <{recurso} />\n  </document-format-change-manifest>", 1)

    # descobre o nome interno de cada fonte de dados e injeta os campos calculados nela
    for chave, tabela in TABELAS.items():
        m = re.search(r"<datasource caption='([^']*" + tabela + r"[^']*)' inline='true' name='(federated\.[^']+)'", twb)
        if not m:
            raise SystemExit(f"Fonte de dados '{tabela}' não encontrada em {ORIGEM.name}")
        g.DS[chave], g.CAPTION[chave] = m.group(2), m.group(1)
        pos = twb.index("      <extract ", m.start())
        twb = twb[:pos] + g.colunas_calculadas(chave) + "\n" + twb[pos:]

    twb = re.sub(r"  <worksheets>.*</windows>", lambda _: g.montar_xml(), twb, flags=re.S)

    with zipfile.ZipFile(DESTINO, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("energia_dashboard.twb", twb)
        for n, dados in outros.items():
            z.writestr(n, dados)
        for p in L.PAGINAS:
            arq = BASE / "tableau" / "assets" / f"fundo_{L.slug(p)}.png"
            z.write(arq, f"Image/{arq.name}")
    print("Dashboard gerado:", DESTINO.relative_to(BASE))


if __name__ == "__main__":
    main()
