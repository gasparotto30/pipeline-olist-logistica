"""Testes unitários do módulo pipeline.marts."""

from pathlib import Path
import pytest
from pipeline.db import get_connection, init_db
from pipeline.marts import executar_marts


def test_arquivo_sem_prefixo_nn_encerra_com_system_exit(tmp_path: Path) -> None:
    sql_dir = tmp_path / "sql"
    sql_dir.mkdir()
    db_file = tmp_path / "test.duckdb"
    
    # Arquivo fora do padrão NN_
    (sql_dir / "kpis_sem_prefixo.sql").write_text("SELECT 1 AS id;", encoding="utf-8")
    
    with pytest.raises(SystemExit):
        executar_marts(db_path=db_file, sql_dir=sql_dir)


def test_mart_vazio_encerra_e_deixa_schema_intacto(tmp_path: Path) -> None:
    sql_dir = tmp_path / "sql"
    sql_dir.mkdir()
    db_file = tmp_path / "test_vazio.duckdb"
    init_db(db_file)
    
    # Cria uma tabela prévia em marts
    with get_connection(db_file, read_only=False) as con:
        con.execute("CREATE TABLE marts.tabela_previa AS SELECT 100 AS valor;")
        
    # SQL que resulta em 0 linhas
    (sql_dir / "01_vazio.sql").write_text("SELECT 1 AS id WHERE 1=0;", encoding="utf-8")
    
    with pytest.raises(SystemExit):
        executar_marts(db_path=db_file, sql_dir=sql_dir)
        
    # Confere se a tabela prévia continuou intacta
    with get_connection(db_file, read_only=True) as con:
        qtd = con.execute("SELECT count(*) FROM marts.tabela_previa;").fetchone()[0]
        assert qtd == 1


def test_regras_de_entrega_no_prazo_com_dados_inventados(tmp_path: Path) -> None:
    sql_dir = tmp_path / "sql"
    sql_dir.mkdir()
    db_file = tmp_path / "test_regras.duckdb"
    init_db(db_file)
    
    with get_connection(db_file, read_only=False) as con:
        # p1: Entregue às 18h do dia previsto -> NO PRAZO
        # p2: Entregue 1 dia após a data prevista -> ATRASADO
        # p3: Cancelado -> FICA FORA de entregas concluídas
        con.execute(
            """
            CREATE TABLE refined.pedidos (
                pedido_id VARCHAR, cliente_id VARCHAR, status VARCHAR,
                data_compra TIMESTAMP, data_aprovacao TIMESTAMP,
                data_envio_transportadora TIMESTAMP, data_entrega TIMESTAMP,
                data_entrega_prevista DATE
            );
            INSERT INTO refined.pedidos VALUES 
                ('p1', 'c1', 'delivered', '2017-01-01 10:00:00', '2017-01-01 11:00:00', '2017-01-02 12:00:00', '2017-01-05 18:00:00', '2017-01-05'),
                ('p2', 'c2', 'delivered', '2017-01-02 09:00:00', '2017-01-02 10:00:00', '2017-01-03 11:00:00', '2017-01-08 10:00:00', '2017-01-07'),
                ('p3', 'c3', 'canceled', '2017-01-03 09:00:00', '2017-01-03 10:00:00', NULL, NULL, '2017-01-10');
            """
        )
        con.execute(
            """
            CREATE TABLE refined.avaliacoes (
                avaliacao_id VARCHAR, pedido_id VARCHAR, nota INT,
                mensagem VARCHAR, data_criacao TIMESTAMP, data_resposta TIMESTAMP
            );
            INSERT INTO refined.avaliacoes VALUES ('a1', 'p1', 5, 'Bom', '2017-01-06', '2017-01-07');
            """
        )
        
    # Copia o sql 01_kpis_logistica
    sql_origem = Path("sql/marts/01_kpis_logistica.sql").read_text(encoding="utf-8")
    (sql_dir / "01_kpis_logistica.sql").write_text(sql_origem, encoding="utf-8")
    
    executar_marts(db_path=db_file, sql_dir=sql_dir)
    
    with get_connection(db_file, read_only=True) as con:
        # Esperado: 2 pedidos entregues (p3 fora), 1 no prazo e 1 atrasado (50% no prazo)
        res = con.execute("SELECT pedidos_entregues, pct_no_prazo FROM marts.kpis_logistica;").fetchone()
        pedidos_entregues, pct_no_prazo = res
        assert pedidos_entregues == 2
        assert pct_no_prazo == 50.0
