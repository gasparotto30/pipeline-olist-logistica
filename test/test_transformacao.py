"""Testes unitários do módulo pipeline.transformacao."""

from pathlib import Path
import pytest
from pipeline.db import get_connection, init_db
from pipeline.transformacao import transformar


def preparar_banco_raw(db_file: Path) -> None:
    init_db(db_file)
    with get_connection(db_file, read_only=False) as con:
        # 1. Pedidos com 1 duplicata exata (3 linhas no raw -> 2 no refined)
        con.execute(
            """
            CREATE TABLE raw.pedidos (
                pedido_id VARCHAR, cliente_id VARCHAR, status VARCHAR,
                data_compra VARCHAR, data_aprovacao VARCHAR,
                data_envio_transportadora VARCHAR, data_entrega VARCHAR,
                data_entrega_prevista VARCHAR
            );
            INSERT INTO raw.pedidos VALUES 
                ('p1', 'c1', 'delivered', '2017-01-01 10:00:00', '2017-01-01 11:00:00', '2017-01-02 12:00:00', '2017-01-05 14:00:00', '2017-01-10'),
                ('p1', 'c1', 'delivered', '2017-01-01 10:00:00', '2017-01-01 11:00:00', '2017-01-02 12:00:00', '2017-01-05 14:00:00', '2017-01-10'),
                ('p2', 'c2', 'shipped', '2017-01-02 09:00:00', '2017-01-02 10:00:00', '2017-01-03 11:00:00', NULL, '2017-01-15');
            """
        )
        con.execute(
            """
            CREATE TABLE raw.clientes (cliente_id VARCHAR, cliente_unico_id VARCHAR, cep VARCHAR, cidade VARCHAR, uf VARCHAR);
            INSERT INTO raw.clientes VALUES ('c1', 'u1', '01001', 'SP', 'SP'), ('c2', 'u2', '20000', 'RJ', 'RJ');
            """
        )
        con.execute(
            """
            CREATE TABLE raw.itens_pedido (pedido_id VARCHAR, item_id VARCHAR, produto_id VARCHAR, vendedor_id VARCHAR, data_envio_limite VARCHAR, preco VARCHAR, frete VARCHAR);
            INSERT INTO raw.itens_pedido VALUES ('p1', '1', 'prod1', 'v1', '2017-01-08 10:00:00', '150.50', '20.00');
            """
        )
        con.execute(
            """
            CREATE TABLE raw.vendedores (vendedor_id VARCHAR, cep VARCHAR, cidade VARCHAR, uf VARCHAR);
            INSERT INTO raw.vendedores VALUES ('v1', '01001', 'SP', 'SP');
            """
        )
        con.execute(
            """
            CREATE TABLE raw.avaliacoes (avaliacao_id VARCHAR, pedido_id VARCHAR, nota VARCHAR, mensagem VARCHAR, data_criacao VARCHAR, data_resposta VARCHAR);
            INSERT INTO raw.avaliacoes VALUES ('a1', 'p1', '5', 'Excelente', '2017-01-06 10:00:00', '2017-01-07 10:00:00');
            """
        )
        con.execute(
            """
            CREATE TABLE raw.pagamentos (pedido_id VARCHAR, sequencia VARCHAR, tipo VARCHAR, parcelas VARCHAR, valor VARCHAR);
            INSERT INTO raw.pagamentos VALUES ('p1', '1', 'credit_card', '2', '170.50');
            """
        )


def test_duplicata_exata_sai_e_tipos_convertem(tmp_path: Path) -> None:
    db_file = tmp_path / "test_transf.duckdb"
    preparar_banco_raw(db_file)
    
    transformar(db_path=db_file)
    
    with get_connection(db_file, read_only=True) as con:
        # Raw tinha 3 pedidos, refined deve ter 2 (duplicata exata descartada)
        qtd_pedidos = con.execute("SELECT count(*) FROM refined.pedidos;").fetchone()[0]
        assert qtd_pedidos == 2
        
        # Validação de tipo: preco deve ser DECIMAL e somar com precisão exata
        preco = con.execute("SELECT preco FROM refined.itens_pedido WHERE pedido_id='p1';").fetchone()[0]
        assert str(preco) == "150.50"


def test_valor_invalido_de_data_encerra_com_system_exit(tmp_path: Path) -> None:
    db_file = tmp_path / "test_invalido.duckdb"
    init_db(db_file)
    with get_connection(db_file, read_only=False) as con:
        # Insere data com texto corrompido que não converte para TIMESTAMP
        con.execute(
            """
            CREATE TABLE raw.pedidos (
                pedido_id VARCHAR, cliente_id VARCHAR, status VARCHAR,
                data_compra VARCHAR, data_aprovacao VARCHAR,
                data_envio_transportadora VARCHAR, data_entrega VARCHAR,
                data_entrega_prevista VARCHAR
            );
            INSERT INTO raw.pedidos VALUES 
                ('p1', 'c1', 'delivered', 'DATA_INVALIDA_CORROMPIDA', NULL, NULL, NULL, '2017-01-10');
            """
        )
        # Cria as demais vazias para satisfazer o fluxo
        for tab in ["clientes", "itens_pedido", "vendedores", "avaliacoes", "pagamentos"]:
            con.execute(f"CREATE TABLE raw.{tab} (col VARCHAR);")

    with pytest.raises(SystemExit):
        transformar(db_path=db_file)

