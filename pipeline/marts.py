"""Módulo executor dos marts SQL do pipeline.

Lê arquivos em sql/marts/*.sql ordenados por prefixo numérico.
Regras da spec:
- Arquivo sem prefixo NN_ para antes de executar (SystemExit).
- Mart vazio encerra e deixa o schema marts como estava.
- Arquivo apagado faz o mart sumir na execução seguinte.
"""

from pathlib import Path
import re
import sys
import duckdb
from pipeline.db import DB_PATH, get_connection

SQL_DIR = Path("sql/marts")


def validar_arquivos(sql_dir: Path = SQL_DIR) -> list[Path]:
    """Valida se todos os arquivos .sql possuem o prefixo numérico NN_."""
    arquivos = list(sql_dir.glob("*.sql"))
    if not arquivos:
        print(f"Erro: nenhum arquivo .sql encontrado em {sql_dir}")
        sys.exit(1)
        
    padrao = re.compile(r"^\d{2}_[a-zA-Z0-9_]+\.sql$")
    for f in arquivos:
        if not padrao.match(f.name):
            print(f"Erro: arquivo {f.name} não segue o padrão de prefixo 'NN_nome.sql'")
            sys.exit(1)
            
    return sorted(arquivos, key=lambda p: p.name)


def extrair_nome_tabela(arquivo: Path) -> str:
    """Extrai o nome da tabela a partir do arquivo (ex: 01_kpis.sql -> kpis)."""
    return re.sub(r"^\d{2}_", "", arquivo.stem)


def executar_marts(db_path: Path | str = DB_PATH, sql_dir: Path = SQL_DIR) -> None:
    """Executa todos os scripts SQL gerando as tabelas no schema marts.*."""
    arquivos = validar_arquivos(sql_dir)
    
    with get_connection(db_path, read_only=False) as con:
        con.execute("CREATE SCHEMA IF NOT EXISTS marts;")
        
        # Tabelas existentes antes de rodar
        tabelas_atuais = set(
            row[0] for row in con.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='marts';"
            ).fetchall()
        )
        
        tabelas_esperadas = set(extrair_nome_tabela(f) for f in arquivos)
        
        # Executamos em schema temporário ou com validação linha a linha
        # Se um mart falhar ou ficar vazio, o schema marts é mantido intacto.
        con.execute("CREATE SCHEMA IF NOT EXISTS temp_marts;")
        
        tabelas_criadas = []
        total_linhas = 0
        
        try:
            for f in arquivos:
                nome_tabela = extrair_nome_tabela(f)
                conteudo_sql = f.read_text(encoding="utf-8")
                
                # Executa criação na área temporária
                con.execute(f"DROP TABLE IF EXISTS temp_marts.{nome_tabela};")
                con.execute(f"CREATE TABLE temp_marts.{nome_tabela} AS {conteudo_sql};")
                
                qtd = con.execute(f"SELECT count(*) FROM temp_marts.{nome_tabela};").fetchone()[0]
                if qtd == 0:
                    print(f"Erro: o mart '{nome_tabela}' gerou 0 linhas. Operação cancelada.")
                    con.execute("DROP SCHEMA IF EXISTS temp_marts CASCADE;")
                    sys.exit(1)
                    
                tabelas_criadas.append((nome_tabela, qtd))
                total_linhas += qtd
                
            # Todas passaram e têm > 0 linhas: sincroniza com marts.*
            for nome_tabela, _ in tabelas_criadas:
                con.execute(f"DROP TABLE IF EXISTS marts.{nome_tabela};")
                con.execute(f"CREATE TABLE marts.{nome_tabela} AS SELECT * FROM temp_marts.{nome_tabela};")
                
            # Arquivo apagado faz o mart sumir
            tabelas_orfas = tabelas_atuais - tabelas_esperadas
            for orfa in tabelas_orfas:
                con.execute(f"DROP TABLE IF EXISTS marts.{orfa};")
                
            con.execute("DROP SCHEMA IF EXISTS temp_marts CASCADE;")
            
            for nome_tabela, qtd in tabelas_criadas:
                print(f"✓ marts.{nome_tabela} {qtd:,} linhas")
            print(f"{len(tabelas_criadas)} marts {total_linhas:,} linhas")
            
        except Exception as e:
            con.execute("DROP SCHEMA IF EXISTS temp_marts CASCADE;")
            print(f"Erro ao executar marts: {e}")
            sys.exit(1)


if __name__ == "__main__":
    executar_marts()
