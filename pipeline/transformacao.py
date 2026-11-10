"""Módulo de transformação do pipeline Olist.

Lê do schema raw.*, remove duplicatas exatas, converte datas para TIMESTAMP e dinheiro para DECIMAL.
Se algum valor não converter, encerra com SystemExit sem mascarar o erro com nulo.
Grava as tabelas limpas no schema refined.*.
"""

from pathlib import Path
import sys
import duckdb
from pipeline.db import DB_PATH, get_connection

TRANSFORMACOES = {
    "pedidos": """
        CREATE TABLE refined.pedidos AS
        SELECT DISTINCT
            pedido_id,
            cliente_id,
            status,
            CAST(data_compra AS TIMESTAMP) AS data_compra,
            CAST(data_aprovacao AS TIMESTAMP) AS data_aprovacao,
            CAST(data_envio_transportadora AS TIMESTAMP) AS data_envio_transportadora,
            CAST(data_entrega AS TIMESTAMP) AS data_entrega,
            CAST(data_entrega_prevista AS DATE) AS data_entrega_prevista
        FROM raw.pedidos;
    """,
    "clientes": """
        CREATE TABLE refined.clientes AS
        SELECT DISTINCT
            cliente_id,
            cliente_unico_id,
            cep,
            cidade,
            uf
        FROM raw.clientes;
    """,
    "itens_pedido": """
        CREATE TABLE refined.itens_pedido AS
        SELECT DISTINCT
            pedido_id,
            CAST(item_id AS INTEGER) AS item_id,
            produto_id,
            vendedor_id,
            CAST(data_envio_limite AS TIMESTAMP) AS data_envio_limite,
            CAST(preco AS DECIMAL(10, 2)) AS preco,
            CAST(frete AS DECIMAL(10, 2)) AS frete
        FROM raw.itens_pedido;
    """,
    "vendedores": """
        CREATE TABLE refined.vendedores AS
        SELECT DISTINCT
            vendedor_id,
            cep,
            cidade,
            uf
        FROM raw.vendedores;
    """,
    "avaliacoes": """
        CREATE TABLE refined.avaliacoes AS
        SELECT DISTINCT
            avaliacao_id,
            pedido_id,
            CAST(nota AS INTEGER) AS nota,
            mensagem,
            CAST(data_criacao AS TIMESTAMP) AS data_criacao,
            CAST(data_resposta AS TIMESTAMP) AS data_resposta
        FROM raw.avaliacoes;
    """,
    "pagamentos": """
        CREATE TABLE refined.pagamentos AS
        SELECT DISTINCT
            pedido_id,
            CAST(sequencia AS INTEGER) AS sequencia,
            tipo,
            CAST(parcelas AS INTEGER) AS parcelas,
            CAST(valor AS DECIMAL(10, 2)) AS valor
        FROM raw.pagamentos;
    """,
}


def transformar(db_path: Path | str = DB_PATH) -> None:
    """Executa a transformação e validação estrita dos dados para refined.*."""
    with get_connection(db_path, read_only=False) as con:
        # Garante schema refined
        con.execute("CREATE SCHEMA IF NOT EXISTS refined;")
        
        for tabela, sql in TRANSFORMACOES.items():
            # Verifica se tabela raw existe
            existe = con.execute(
                f"SELECT count(*) FROM information_schema.tables WHERE table_schema='raw' AND table_name='{tabela}';"
            ).fetchone()[0]
            if not existe:
                print(f"Erro: tabela raw.{tabela} não existe para transformação.")
                sys.exit(1)
            
            try:
                con.execute(f"DROP TABLE IF EXISTS refined.{tabela};")
                con.execute(sql)
                qtd = con.execute(f"SELECT count(*) FROM refined.{tabela};").fetchone()[0]
                print(f"✓ refined.{tabela} ({qtd:,} linhas)")
            except Exception as e:
                print(f"Erro na transformação de {tabela}: {e}")
                sys.exit(1)


if __name__ == "__main__":
    transformar()
