-- Evolução mensal de volume de entregas e cumprimento de SLA
-- Grão: um ano e mês de compra do pedido.
SELECT
    strftime(data_compra, '%Y-%m') AS ano_mes,
    count(*) AS pedidos_entregues,
    count(*) FILTER (WHERE data_entrega::DATE <= data_entrega_prevista) AS pedidos_no_prazo,
    round(100.0 * count(*) FILTER (WHERE data_entrega::DATE <= data_entrega_prevista) / count(*), 1) AS pct_no_prazo,
    round(avg(date_diff('day', data_compra, data_entrega)), 1) AS dias_medio_entrega
FROM refined.pedidos
WHERE status = 'delivered'
  AND data_entrega IS NOT NULL
  AND data_compra IS NOT NULL
GROUP BY strftime(data_compra, '%Y-%m')
ORDER BY ano_mes ASC;

