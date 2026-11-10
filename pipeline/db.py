"""Módulo de conexão e gerenciamento do banco DuckDB.

Garante criação dos schemas e gerenciamento de conexões fechadas pontualmente.
"""

from pathlib import Path
import duckdb

DB_PATH = Path("olist.duckdb")


def get_connection(db_path: Path | str = DB_PATH, read_only: bool = False) -> duckdb.DuckDBPyConnection:
    """Retorna uma conexão DuckDB.
    
    Abre e fecha conforme o contexto. Em consultas de dashboard, use read_only=True.
    """
    path_str = str(db_path)
    return duckdb.connect(path_str, read_only=read_only)


def init_db(db_path: Path | str = DB_PATH) -> None:
    """Inicializa os schemas essenciais do pipeline."""
    with get_connection(db_path, read_only=False) as con:
        con.execute("CREATE SCHEMA IF NOT EXISTS raw;")
        con.execute("CREATE SCHEMA IF NOT EXISTS refined;")
        con.execute("CREATE SCHEMA IF NOT EXISTS marts;")
