-- KPIs gerais de Logística e Experiência do Cliente
-- Grão: a operação inteira, exatamente uma linha.
WITH entregas AS (
    SELECT
        pedido_id,
        date_diff('day', data_compra, data_entrega) AS dias_espera,
        date_diff('day', data_entrega::DATE, data_entrega_prevista) AS dias_antecipacao,
        CASE WHEN data_entrega::DATE <= data_entrega_prevista THEN 1 ELSE 0 END AS no_prazo
    FROM refined.pedidos
    WHERE status = 'delivered'
      AND data_entrega IS NOT NULL
      AND data_compra IS NOT NULL
),
avaliacoes_entregues AS (
    SELECT
        e.pedido_id,
        avg(a.nota) AS nota
    FROM entregas e
    JOIN refined.avaliacoes a ON a.pedido_id = e.pedido_id
    GROUP BY e.pedido_id
)
SELECT
    count(e.pedido_id) AS pedidos_entregues,
    round(100.0 * sum(e.no_prazo) / count(*), 1) AS pct_no_prazo,
    round(avg(e.dias_espera), 1) AS dias_medio_entrega,
    median(e.dias_espera) AS dias_mediana_entrega,
    round(avg(e.dias_antecipacao), 1) AS dias_medio_antecipacao,
    round(avg(a.nota), 2) AS nota_media,
    round(100.0 * count(*) FILTER (WHERE a.nota <= 2) / count(a.pedido_id), 1) AS pct_nota_baixa
FROM entregas e
LEFT JOIN avaliacoes_entregues a ON a.pedido_id = e.pedido_id;

