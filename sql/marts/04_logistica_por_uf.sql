-- Indicadores logísticos consolidados por Estado (UF) do cliente
-- Grão: uma UF do cliente.
SELECT
    c.uf,
    count(*) AS entregues,
    round(100.0 * count(*) FILTER (WHERE p.data_entrega::DATE <= p.data_entrega_prevista) / count(*), 1) AS pct_no_prazo,
    round(avg(date_diff('day', p.data_compra, p.data_entrega)), 1) AS dias_medio_real,
    round(avg(date_diff('day', p.data_compra, p.data_entrega_prevista)), 1) AS dias_medio_previsto,
    round(avg(date_diff('day', p.data_entrega::DATE, p.data_entrega_prevista)), 1) AS dias_delta_medio
FROM refined.pedidos p
JOIN refined.clientes c ON c.cliente_id = p.cliente_id
WHERE p.status = 'delivered'
  AND p.data_entrega IS NOT NULL
  AND p.data_compra IS NOT NULL
GROUP BY c.uf
ORDER BY pct_no_prazo DESC, entregues DESC;
