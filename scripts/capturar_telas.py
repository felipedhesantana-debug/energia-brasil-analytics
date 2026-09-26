"""Tira prints das 3 páginas do dashboard (Tableau em modo apresentação) para a documentação.
Uso: rode este arquivo e, em até 15 s, deixe o Tableau em tela cheia na página Preço."""
import subprocess
import time
from pathlib import Path

PASTA = Path(__file__).resolve().parents[1] / "docs" / "img"
PASTA.mkdir(parents=True, exist_ok=True)
for i, pagina in enumerate(["preco", "matriz", "reservatorios"]):
    time.sleep(20 if i == 0 else 15)
    destino = PASTA / f"dashboard_{pagina}.png"
    subprocess.run(["screencapture", "-x", str(destino)], check=True)
    print("capturado:", destino.name, flush=True)
