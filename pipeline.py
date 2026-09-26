"""
Pipeline completo do projeto Energia no Brasil (ONS).

No VS Code: abra este arquivo e clique em ▶ (Run Python File).
No terminal:  python3 pipeline.py            -> roda tudo
              python3 pipeline.py dbt        -> só uma etapa (setup | notebook | dbt | export | kpis)

Etapas:
  0. setup     cria o ambiente virtual (.venv) e instala as dependências
  1. notebook  executa notebooks/01_ingestao_limpeza.ipynb (baixa dados do ONS; bronze + silver no DuckDB)
  2. dbt       dbt build: modelos staging -> intermediate -> gold + testes de qualidade
  3. export    exporta a camada gold para CSV (fonte do Tableau)
  4. kpis      mostra o resumo anual (preço, matriz e reservatórios)
"""
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
VENV = BASE / ".venv"
BIN = VENV / ("Scripts" if os.name == "nt" else "bin")
PY = BIN / "python"
LOG = BASE / "logs" / "pipeline.log"
LOG.parent.mkdir(exist_ok=True)
_log = open(LOG, "w", encoding="utf-8")


def mostrar(txt):
    print(txt, end="", flush=True)
    _log.write(txt)
    _log.flush()


def rodar(cmd, cwd=BASE, env=None):
    """Executa um comando mostrando a saída na tela e gravando em logs/pipeline.log."""
    mostrar(f"\n$ {' '.join(str(c).replace(str(BASE) + '/', '') for c in cmd)}\n")
    proc = subprocess.Popen([str(c) for c in cmd], cwd=cwd, env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for linha in proc.stdout:
        mostrar(linha)
    if proc.wait() != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd)


def etapa(titulo):
    mostrar(f"\n{'=' * 60}\n{titulo}\n{'=' * 60}\n")


def versao(python):
    """Retorna (major, minor) de um interpretador Python, ou None."""
    try:
        out = subprocess.run([str(python), "-c", "import sys; print(sys.version_info[0], sys.version_info[1])"],
                             capture_output=True, text=True, check=True).stdout.split()
        return int(out[0]), int(out[1])
    except Exception:
        return None


def suportado(v):
    # dbt ainda não suporta as versões mais novas do Python
    return v is not None and (3, 9) <= v <= (3, 12)


def escolher_python():
    candidatos = ["python3.12", "python3.11", "python3.10", "/opt/homebrew/bin/python3.12",
                  "/opt/homebrew/bin/python3.11", "/usr/local/bin/python3.12", "/usr/local/bin/python3.11",
                  sys.executable, "/usr/bin/python3", "python3"]
    for c in candidatos:
        caminho = shutil.which(c) or (c if Path(c).exists() else None)
        if caminho and suportado(versao(caminho)):
            return caminho
    raise SystemExit("Nenhum Python entre 3.9 e 3.12 encontrado (o dbt ainda não roda no 3.13+).")


def setup():
    etapa("0. Ambiente Python (.venv)")
    if PY.exists() and not suportado(versao(PY)):
        mostrar(f"O .venv atual usa Python {versao(PY)}, que o dbt não suporta. Recriando...\n")
        shutil.rmtree(VENV)
    if not PY.exists():
        base = escolher_python()
        mostrar(f"Criando .venv com {base} (Python {'.'.join(map(str, versao(base)))})\n")
        rodar([base, "-m", "venv", VENV])
    try:
        rodar([PY, "-c", "import duckdb, dbt.version, nbconvert, ipykernel, openpyxl"])
        mostrar("Dependências já instaladas.\n")
    except subprocess.CalledProcessError:
        rodar([PY, "-m", "pip", "install", "-q", "--upgrade", "pip"])
        rodar([PY, "-m", "pip", "install", "-q", "-r", "requirements.txt"])
    rodar([BIN / "dbt", "--version"])


def notebook():
    etapa("1. Notebook: ingestão e limpeza (camadas bronze e silver)")
    rodar([BIN / "jupyter", "nbconvert", "--to", "notebook", "--execute", "--inplace",
           "--ExecutePreprocessor.kernel_name=python3", "--ExecutePreprocessor.timeout=1800", "notebooks/01_ingestao_limpeza.ipynb"])


def dbt():
    etapa("2. dbt build: modelagem (staging -> intermediate -> gold) + testes")
    env = {**os.environ, "DBT_PROFILES_DIR": str(BASE / "dbt")}
    rodar([BIN / "dbt", "build"], cwd=BASE / "dbt", env=env)
    rodar([BIN / "dbt", "docs", "generate", "--static"], cwd=BASE / "dbt", env=env)
    mostrar("Documentação do dbt: dbt/target/static_index.html\n")


def export():
    etapa("3. Export da camada gold para o Tableau")
    rodar([PY, "scripts/exportar_tableau.py"])


def kpis():
    etapa("4. Resumo anual (gold.mart_resumo_anual)")
    rodar([PY, "-c", "import duckdb; print(duckdb.connect('data/energia.duckdb', read_only=True)"
                     ".sql('select * from gold.mart_resumo_anual'))"])


ETAPAS = {"setup": setup, "notebook": notebook, "dbt": dbt, "export": export, "kpis": kpis}

if __name__ == "__main__":
    inicio = time.time()
    escolhidas = sys.argv[1:] or list(ETAPAS)
    if escolhidas != ["setup"] and "setup" not in escolhidas and not PY.exists():
        escolhidas = ["setup"] + escolhidas
    try:
        for nome in escolhidas:
            ETAPAS[nome]()
        mostrar(f"\nPIPELINE OK ✅  ({time.time() - inicio:.0f}s)\n")
    except subprocess.CalledProcessError as erro:
        mostrar(f"\nPIPELINE FALHOU ❌  comando: {erro.cmd}\n")
        sys.exit(1)
