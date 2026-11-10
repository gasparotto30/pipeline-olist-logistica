"""Testes unitários do módulo pipeline.ingestao."""

from pathlib import Path
import pytest
from pipeline.ingestao import ingerir, TABELAS_ESPERADAS
from pipeline.db import get_connection


def test_csv_vira_tabela_com_mesmas_linhas(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    db_file = tmp_path / "test_ingestao.duckdb"
    
    # Cria arquivos sintéticos pequenos para cada tabela esperada
    for tab in TABELAS_ESPERADAS:
        csv_file = raw_dir / f"{tab}.csv"
        # 3 linhas (cabeçalho + 2 registros sintéticos)
        csv_file.write_text("col1,col2\nval1,val2\nval3,val4\n", encoding="utf-8")
        
    ingerir(db_path=db_file, raw_dir=raw_dir)
    
    with get_connection(db_file, read_only=True) as con:
        for tab in TABELAS_ESPERADAS:
            qtd = con.execute(f"SELECT count(*) FROM raw.{tab};").fetchone()[0]
            # Deve conter exatamente 2 linhas de dados
            assert qtd == 2


def test_arquivo_faltando_encerra_com_system_exit(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw_incompleto"
    raw_dir.mkdir()
    db_file = tmp_path / "test_falta.duckdb"
    
    # Cria apenas uma das tabelas esperadas, deixando as demais faltando
    (raw_dir / "pedidos.csv").write_text("id,status\n1,delivered\n", encoding="utf-8")
    
    with pytest.raises(SystemExit):
        ingerir(db_path=db_file, raw_dir=raw_dir)

