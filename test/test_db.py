"""Testes unitários do módulo pipeline.db."""

from pathlib import Path
from pipeline.db import get_connection, init_db


def test_init_db_cria_schemas_raw_refined_marts(tmp_path: Path) -> None:
    # Banco isolado temporário dentro de tmp_path
    db_file = tmp_path / "test.duckdb"
    
    init_db(db_file)
    
    # Valida se os 3 schemas foram criados corretamente
    with get_connection(db_file, read_only=True) as con:
        schemas = [
            row[0]
            for row in con.execute(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name IN ('raw', 'refined', 'marts');"
            ).fetchall()
        ]
        
    assert "raw" in schemas
    assert "refined" in schemas
    assert "marts" in schemas


def test_conexao_read_only_impede_escrita(tmp_path: Path) -> None:
    db_file = tmp_path / "test_ro.duckdb"
    init_db(db_file)
    
    # Com conexão read_only=True, operações de escrita devem falhar
    with get_connection(db_file, read_only=True) as con:
        try:
            con.execute("CREATE TABLE marts.teste (id INT);")
            escreveu = True
        except Exception:
            escreveu = False
            
    assert not escreveu
