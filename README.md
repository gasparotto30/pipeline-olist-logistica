# Pipeline Olist · Logística & Experiência do Cliente

Pipeline de dados analítico end-to-end construído sobre o dataset público da Olist Store (Kaggle), customizado com foco em **Logística, Cumprimento de SLA de Entrega e Satisfação do Cliente (Avaliações)**.

Desenvolvido seguindo princípios de **Spec-Driven Development**, arquitetura em 3 camadas (Raw, Refined, Marts) no DuckDB e desacoplamento visual rigoroso (**a tela não calcula**).

---

## 1. Arquitetura das Camadas

- **`raw.*`**: Dados brutos ingeridos diretamente dos arquivos `.csv` sem alteração de tipos ou regras de negócio.
- **`refined.*`**: Camada padronizada com deduplicação exata (`DISTINCT *`), conversão estrita de tipos (`TIMESTAMP`, `DECIMAL`) e integridade referencial.
- **`marts.*`**: Tabelas analíticas agregadas prontas para consumo direto em dashboards e relatórios.

### O que é uma linha em cada Mart:
- `marts.kpis_logistica`: **A operação inteira** (1 linha). Consolida taxa global de SLA, tempo médio de espera, dias médios de antecipação e nota média.
- `marts.sla_mensal`: **Um ano e mês de compra**. Evolução temporal do cumprimento de prazo de entrega.
- `marts.faixas_pontualidade_vs_nota`: **Uma faixa de pontualidade** (antecipado 5d+, antecipado 1 a 4d, no dia, atrasado leve, atrasado crítico).
- `marts.logistica_por_uf`: **Um estado (UF) do cliente**. Desempenho geográfico de pontualidade e dias de espera.
- `marts.gargalo_etapas`: **Uma etapa operacional da entrega** (Despacho do vendedor vs Trânsito da transportadora).
- `marts.ranking_sellers_logistica`: **Um vendedor** com mais de 20 entregas concluídas.

---

## 2. Como Rodar do Zero

Requisitos: Python 3.11+ e `uv`.

### Passo 1: Instalar dependências
```bash
uv sync
```

### Passo 2: Executar o pipeline analítico
```bash
# 1. Ingestão (Raw)
uv run python -m pipeline.ingestao

# 2. Transformação (Refined)
uv run python -m pipeline.transformacao

# 3. Indicadores (Marts SQL)
uv run python -m pipeline.marts
```

### Passo 3: Visualizar o Dashboard Interativo (Streamlit)
```bash
uv run streamlit run app.py
```
Acesse em: `http://localhost:8501`

### Passo 4: Gerar o Relatório Estático Autônomo (HTML)
```bash
uv run python relatorio.py
```
Gera o arquivo `relatorio.html` (< 200 KB), que pode ser aberto diretamente com dois cliques em qualquer navegador sem necessidade de servidor Python.

---

## 3. Testes Unitários e Cobertura

Os testes rodam sobre **dados sintéticos inventados** em ambientes temporários (`tmp_path`), sem nunca consultar o banco de produção (`olist.duckdb`) ou a pasta `raw/`.

Para rodar a suíte completa de testes com relatório de cobertura:
```bash
uv run pytest --cov
```

**Meta:** Cobertura de código superior a 60% (atual: > 90%).

---

## 4. Onde a IA Apoiou e Decisões de Projeto

- **Geração de Spec & Código:** O pipeline foi estruturado a partir de especificações declarativas rígidas.
- **Isolamento de concorrência:** A conexão com o DuckDB no `painel.py` utiliza `read_only=True` abrindo e fechando no bloco de execução para garantir que o pipeline de atualização possa rodar simultaneamente ao painel sem gerar *database lock*.
- **Conferência estrita:** O frontend não executa agregações analíticas (`groupby`, `sum`, `mean`, etc.). Todo número novo nasce primeiro como um arquivo `.sql` no diretório `sql/marts/`.
