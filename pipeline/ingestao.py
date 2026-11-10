"""Módulo de ingestão do pipeline Olist.

Lê arquivos CSV (.csv ou .csv.gz) do diretório raw/ e grava tabelas idênticas no schema raw.*.
Se algum arquivo esperado não for encontrado, encerra com SystemExit(1).
"""

from pathlib import Path
import sys
import duckdb
from pipeline.db import DB_PATH, get_connection, init_db

RAW_DIR = Path("raw")

TABELAS_ESPERADAS = [
    "pedidos",
    "itens_pedido",
    "clientes",
    "vendedores",
    "avaliacoes",
    "pagamentos",
]


def localizar_arquivo(nome_tabela: str, raw_dir: Path = RAW_DIR) -> Path:
    """Encontra o arquivo correspondente (.csv ou .csv.gz) ou encerra com erro."""
    candidatos = [
        raw_dir / f"{nome_tabela}.csv",
        raw_dir / f"{nome_tabela}.csv.gz",
        raw_dir / f"olist_{nome_tabela}_dataset.csv",
        raw_dir / f"olist_{nome_tabela}_dataset.csv.gz",
    ]
    for p in candidatos:
        if p.exists() and p.is_file():
            return p
    print(f"Erro: Arquivo bruto para a tabela '{nome_tabela}' não encontrado em {raw_dir}")
    sys.exit(1)


def ingerir(db_path: Path | str = DB_PATH, raw_dir: Path = RAW_DIR) -> None:
    """Carrega os arquivos brutos para o schema raw.* sem alteração de tipos ou dados."""
    init_db(db_path)
    
    with get_connection(db_path, read_only=False) as con:
        for tabela in TABELAS_ESPERADAS:
            caminho = localizar_arquivo(tabela, raw_dir)
            # Lê CSV diretamente no DuckDB criando raw.<tabela>
            caminho_escapado = str(caminho).replace("\\", "/")
            con.execute(f"DROP TABLE IF EXISTS raw.{tabela};")
            con.execute(
                f"""
                CREATE TABLE raw.{tabela} AS 
                SELECT * FROM read_csv_auto('{caminho_escapado}', all_varchar=True);
                """
            )
            qtd = con.execute(f"SELECT count(*) FROM raw.{tabela};").fetchone()[0]
            print(f"✓ raw.{tabela} ({qtd:,} linhas)")


if __name__ == "__main__":
    ingerir()

