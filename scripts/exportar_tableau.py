"""Exporta a camada gold para o Tableau (Excel preserva os tipos numéricos no Tableau em português)."""
from pathlib import Path

import duckdb

BASE = Path(__file__).resolve().parents[1]
SAIDA = BASE / "tableau" / "dados"
SAIDA.mkdir(parents=True, exist_ok=True)

con = duckdb.connect(str(BASE / "data" / "energia.duckdb"), read_only=True)
for t in ["mart_energia_dashboard", "mart_matriz_perfil", "mart_resumo_anual"]:
    df = con.execute(f"SELECT * FROM gold.{t}").df()
    df = df.round(2)  # arquivo menor e sem ruído de ponto flutuante
    df.to_excel(SAIDA / f"{t}.xlsx", index=False, sheet_name=t[:31])
    df.to_csv(SAIDA / f"{t}.csv", index=False)
    print(f"{t}: {len(df):,} linhas -> tableau/dados/{t}.xlsx")
con.close()
