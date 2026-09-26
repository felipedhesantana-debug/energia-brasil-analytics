"""Gera notebooks/01_ingestao_limpeza.ipynb (roda no Google Colab ou localmente)."""
import json
from pathlib import Path

cells = []


def md(t):
    cells.append({"cell_type": "markdown", "metadata": {}, "source": t.strip("\n").splitlines(True)})


def code(t):
    cells.append({"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
                  "source": t.strip("\n").splitlines(True)})


md("""
# ⚡ Energia no Brasil — 01. Ingestão e Limpeza

**Pergunta de negócio:** *por que a energia fica cara no Brasil?* Como o nível dos reservatórios, as chuvas e o avanço da energia solar e eólica mexem com o custo da energia hora a hora.

**Fontes oficiais (ONS — Operador Nacional do Sistema Elétrico, dados abertos):**

| Dataset | Granularidade | O que tem |
|---|---|---|
| Balanço de Energia nos Subsistemas | horária | geração hidrelétrica, térmica, eólica e solar, carga e intercâmbio (MWmed) |
| CMO Semi-horário | 30 min | Custo Marginal de Operação (R$/MWh) — sinal de preço que dá origem ao PLD |
| EAR Diário por Subsistema | diária | energia armazenada nos reservatórios (% da capacidade) |
| ENA Diário por Subsistema | diária | energia natural afluente — "quanta chuva virou água nos rios" (% da média histórica) |

Período: **jan/2020 até o último dado publicado**.

Arquitetura (*medallion*): 🥉 `bronze` (arquivos como vieram) → 🥈 `silver` (limpo, este notebook) → 🥇 `gold` (modelado pelo **dbt**).
""")

code("""
# ---------- 1. Ambiente ----------
import sys, subprocess, ssl, urllib.request, datetime as dt
from pathlib import Path

EM_COLAB = "google.colab" in sys.modules
if EM_COLAB:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "duckdb"], check=True)
    BASE = Path("/content/energia-brasil-analytics")
else:
    BASE = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()

PASTA_RAW = BASE / "data" / "raw"
ARQUIVO_DB = BASE / "data" / "energia.duckdb"
PASTA_RAW.mkdir(parents=True, exist_ok=True)

import numpy as np
import pandas as pd
import duckdb

ANO_INICIAL, ANO_FINAL = 2020, dt.date.today().year
print("Ambiente:", "Google Colab" if EM_COLAB else "local", "| anos:", ANO_INICIAL, "a", ANO_FINAL)
""")

md("""
## 2. Extração
Os arquivos ficam num bucket público do ONS na AWS (`ons-aws-prod-opendata`), um arquivo por ano.
Anos já baixados são reaproveitados — só o ano corrente é baixado de novo (ele é atualizado todo dia).
""")

code("""
# ---------- 2. Download ----------
S3 = "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/"
DATASETS = {
    "balanco": "balanco_energia_subsistema_ho/BALANCO_ENERGIA_SUBSISTEMA_{ano}.csv",
    "cmo":     "cmo_tm/CMO_SEMIHORARIO_{ano}.csv",
    "ear":     "ear_subsistema_di/EAR_DIARIO_SUBSISTEMA_{ano}.csv",
    "ena":     "ena_subsistema_di/ENA_DIARIO_SUBSISTEMA_{ano}.csv",
}

try:
    import certifi
    CONTEXTO = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    CONTEXTO = ssl.create_default_context()

def baixar(nome, caminho, ano):
    destino = PASTA_RAW / nome / Path(caminho.format(ano=ano)).name
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists() and ano < ANO_FINAL:
        return destino, "cache"
    req = urllib.request.Request(S3 + caminho.format(ano=ano), headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=CONTEXTO, timeout=120) as resp:
        destino.write_bytes(resp.read())
    return destino, "baixado"

log = []
for nome, caminho in DATASETS.items():
    for ano in range(ANO_INICIAL, ANO_FINAL + 1):
        arq, status = baixar(nome, caminho, ano)
        log.append({"dataset": nome, "ano": ano, "status": status, "MB": round(arq.stat().st_size / 1e6, 2)})
pd.DataFrame(log).pivot(index="ano", columns="dataset", values="MB")
""")

code("""
# Leitura (separador ';' e ponto decimal)
def ler(nome):
    partes = []
    for arq in sorted((PASTA_RAW / nome).glob("*.csv")):
        df = pd.read_csv(arq, sep=";", dtype=str)
        df["arquivo_origem"] = arq.name
        partes.append(df)
    return pd.concat(partes, ignore_index=True)

bruto = {nome: ler(nome) for nome in DATASETS}
pd.DataFrame({"dataset": list(bruto), "linhas": [len(d) for d in bruto.values()],
              "colunas": [list(d.columns[:-1]) for d in bruto.values()]})
""")

md("## 3. Perfil dos dados (antes da limpeza)")

code("""
# ---------- 3. Profiling ----------
num = {
    "balanco": ["val_gerhidraulica", "val_gertermica", "val_gereolica", "val_gersolar", "val_carga", "val_intercambio"],
    "cmo": ["val_cmo"],
    "ear": ["ear_max_subsistema", "ear_verif_subsistema_mwmes", "ear_verif_subsistema_percentual"],
    "ena": ["ena_bruta_regiao_mwmed", "ena_bruta_regiao_percentualmlt", "ena_armazenavel_regiao_mwmed", "ena_armazenavel_regiao_percentualmlt"],
}
chave = {"balanco": ["id_subsistema", "din_instante"], "cmo": ["id_subsistema", "din_instante"],
         "ear": ["id_subsistema", "ear_data"], "ena": ["id_subsistema", "ena_data"]}

perfil = []
for nome, df in bruto.items():
    valores = df[num[nome]].apply(pd.to_numeric, errors="coerce")
    perfil.append({
        "dataset": nome,
        "linhas": len(df),
        "chaves_duplicadas": int(df.duplicated(chave[nome]).sum()),
        "nulos_numericos": int(valores.isna().sum().sum()),
        "negativos": int((valores < 0).sum().sum()),
        "codigos_subsistema": ", ".join(repr(x) for x in sorted(df["id_subsistema"].unique())),
    })
pd.DataFrame(perfil)
""")

code("""
# O CMO tem valores estranhos? (picos absurdos e negativos)
cmo = pd.to_numeric(bruto["cmo"]["val_cmo"], errors="coerce")
print(cmo.describe().round(2).to_string())
print("\\nCMO > R$ 5.000/MWh:", int((cmo > 5000).sum()), "registros")
print("CMO < 0:", int((cmo < 0).sum()), "registros")
bruto["cmo"].assign(val=cmo).nlargest(5, "val")[["id_subsistema", "din_instante", "val"]]
""")

md("""
## 4. Limpeza (camada silver)

| Problema | Tratamento |
|---|---|
| Tudo chega como texto, com espaços | Tipagem (datas e números) e `strip` |
| Registros repetidos (o ONS republica dados revisados) | Mantém a última versão de cada subsistema + instante |
| CMO com picos impossíveis (ex.: > R$ 5.000/MWh, acima do teto regulatório) | Valor anulado e marcado com `flag_cmo_outlier` |
| CMO negativo (excesso de oferta renovável) | Mantido — é um fenômeno real — e marcado com `flag_cmo_negativo` |
| Balanço inclui a linha "SIN" (soma do país) | Separada com `flag_sin` para não contar em dobro |
| Códigos com espaços sobrando nos arquivos mais recentes (`"N  "` em vez de `"N"`) — pego pelos testes do dbt | `strip` em todas as colunas de texto |
| Nomes de subsistema diferentes entre datasets (`SUDESTE` x `SUDESTE/CENTRO-OESTE`) | Padronizados pelo código (`SE`, `S`, `NE`, `N`) |
| Horas faltando na série | Contadas e reportadas (sem inventar dado) |
""")

code("""
# ---------- 4. Limpeza ----------
TETO_CMO = 5000   # R$/MWh — acima disso consideramos erro de publicação
silver = {}

def base(df, col_data):
    df = df.copy()
    for c in df.columns:
        # arquivos recentes vêm com espaços ("N  ") -> sem isso os joins entre anos quebram
        if pd.api.types.is_string_dtype(df[c]) or df[c].dtype == object:
            df[c] = df[c].astype("string").str.strip()
    df[col_data] = pd.to_datetime(df[col_data], errors="coerce")
    df = df.dropna(subset=[col_data])
    return df

# Balanço horário
b = base(bruto["balanco"], "din_instante")
b[num["balanco"]] = b[num["balanco"]].apply(pd.to_numeric, errors="coerce")
b = b.sort_values("arquivo_origem").drop_duplicates(chave["balanco"], keep="last")
b["flag_sin"] = b["id_subsistema"].eq("SIN")
silver["balanco_horario"] = b.drop(columns="nom_subsistema")

# CMO semi-horário
c = base(bruto["cmo"], "din_instante")
c["val_cmo"] = pd.to_numeric(c["val_cmo"], errors="coerce")
c = c.sort_values("arquivo_origem").drop_duplicates(chave["cmo"], keep="last")
c["flag_cmo_outlier"] = c["val_cmo"].abs() > TETO_CMO
c["flag_cmo_negativo"] = c["val_cmo"] < 0
c.loc[c["flag_cmo_outlier"], "val_cmo"] = np.nan
silver["cmo_semihorario"] = c.drop(columns="nom_subsistema")

# EAR diário
e = base(bruto["ear"], "ear_data")
e[num["ear"]] = e[num["ear"]].apply(pd.to_numeric, errors="coerce")
e = e.sort_values("arquivo_origem").drop_duplicates(chave["ear"], keep="last")
silver["ear_diario"] = e.drop(columns="nom_subsistema")

# ENA diário
n = base(bruto["ena"], "ena_data")
n[num["ena"]] = n[num["ena"]].apply(pd.to_numeric, errors="coerce")
n = n.sort_values("arquivo_origem").drop_duplicates(chave["ena"], keep="last")
silver["ena_diario"] = n.drop(columns="nom_subsistema")

# Subsistemas (dimensão)
silver["subsistemas"] = pd.DataFrame({
    "id_subsistema": ["SE", "S", "NE", "N"],
    "subsistema": ["Sudeste/Centro-Oeste", "Sul", "Nordeste", "Norte"],
})

# Horas faltando no balanço (por subsistema)
esperado = pd.date_range(b["din_instante"].min(), b["din_instante"].max(), freq="h")
faltando = {s: len(esperado.difference(g["din_instante"])) for s, g in b.groupby("id_subsistema")}
print("Horas faltando no balanço por subsistema:", faltando)
print("CMO anulados por outlier:", int(c["flag_cmo_outlier"].sum()), "| CMO negativos (mantidos):", int(c["flag_cmo_negativo"].sum()))

pd.DataFrame({"tabela": list(silver), "linhas": [len(d) for d in silver.values()]})
""")

md("## 5. Testes de qualidade")

code("""
# ---------- 5. Validações ----------
def checar(ok, msg):
    print(("✅ " if ok else "❌ ") + msg)
    assert ok, msg

bh, cm, ea = silver["balanco_horario"], silver["cmo_semihorario"], silver["ear_diario"]
checar(not bh.duplicated(chave["balanco"]).any(), "balanço: 1 registro por subsistema e hora")
checar(not cm.duplicated(chave["cmo"]).any(), "CMO: 1 registro por subsistema e meia hora")
checar(set(cm["id_subsistema"]) <= {"SE", "S", "NE", "N"}, "CMO: só os 4 subsistemas")
checar((bh[num["balanco"][:5]].fillna(0) >= 0).all().all(), "geração e carga nunca negativas")
checar(ea["ear_verif_subsistema_percentual"].between(0, 100).all(), "reservatórios entre 0% e 100%")
checar(cm["val_cmo"].dropna().abs().le(TETO_CMO).all(), f"CMO dentro de ±R$ {TETO_CMO}/MWh")

# Balanço energético: geração = carga + intercâmbio (tolerância de 2%)
sub = bh[~bh["flag_sin"]]
geracao = sub[["val_gerhidraulica", "val_gertermica", "val_gereolica", "val_gersolar"]].sum(axis=1)
erro = (geracao - sub["val_carga"] - sub["val_intercambio"]).abs() / sub["val_carga"]
checar((erro < 0.02).mean() > 0.99, f"balanço fecha em {100*(erro < 0.02).mean():.2f}% das horas")
""")

md("## 6. Carga no DuckDB (bronze + silver)\nDepois é só abrir `data/energia.duckdb` no **DBeaver**.")

code("""
# ---------- 6. Carga ----------
ARQUIVO_DB.unlink(missing_ok=True)
con = duckdb.connect(str(ARQUIVO_DB))
con.execute("CREATE SCHEMA bronze; CREATE SCHEMA silver;")
for nome in DATASETS:
    con.execute(f\"\"\"CREATE TABLE bronze.{nome} AS
        SELECT *, filename AS arquivo_origem FROM read_csv('{(PASTA_RAW / nome).as_posix()}/*.csv',
        delim=';', header=true, all_varchar=true, filename=true)\"\"\")
for nome, df in silver.items():
    con.register("tmp", df)
    con.execute(f"CREATE TABLE silver.{nome} AS SELECT * FROM tmp")
    con.unregister("tmp")
resumo = con.execute("SELECT schema_name AS camada, table_name AS tabela, estimated_size AS linhas FROM duckdb_tables() ORDER BY 1, 2").df()
con.close()
resumo
""")

md("""
## 7. Próximos passos
1. `dbt build` → camada **gold** (fatos horários, hidrologia, marts do dashboard) + testes.
2. `sql/analises.sql` no DBeaver.
3. `python scripts/exportar_tableau.py` → base do Tableau.
""")

code("""
# Em Colab: True para baixar o banco e usar no dbt/DBeaver do seu computador
BAIXAR_BANCO = False
if EM_COLAB and BAIXAR_BANCO:
    from google.colab import files
    files.download(str(ARQUIVO_DB))
""")

nb = {"cells": cells, "metadata": {"colab": {"provenance": []},
      "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
      "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
for i, c in enumerate(nb["cells"]):
    c["id"] = f"cell-{i:02d}"
destino = Path(__file__).resolve().parents[1] / "notebooks" / "01_ingestao_limpeza.ipynb"
destino.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print("Notebook gerado:", destino)
