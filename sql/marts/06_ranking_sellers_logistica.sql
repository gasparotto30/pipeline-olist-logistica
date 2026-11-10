-- Ranking de vendedores com foco em cumprimento de prazo
-- Grão: um vendedor com ao menos 20 entregas concluídas.
WITH pedidos_vendedor AS (
    SELECT DISTINCT
        i.vendedor_id,
        p.pedido_id,
        p.data_compra,
        p.data_entrega,
        CASE WHEN p.data_entrega::DATE <= p.data_entrega_prevista THEN 1 ELSE 0 END AS no_prazo,
        date_diff('day', p.data_compra, p.data_entrega) AS dias_entrega
    FROM refined.itens_pedido i
    JOIN refined.pedidos p ON p.pedido_id = i.pedido_id
    WHERE p.status = 'delivered'
      AND p.data_entrega IS NOT NULL
      AND p.data_compra IS NOT NULL
)
SELECT
    pv.vendedor_id,
    v.uf,
    count(*) AS pedidos_entregues,
    round(100.0 * sum(pv.no_prazo) / count(*), 1) AS pct_no_prazo,
    round(avg(pv.dias_entrega), 1) AS dias_medio_entrega
FROM pedidos_vendedor pv
JOIN refined.vendedores v ON v.vendedor_id = pv.vendedor_id
GROUP BY pv.vendedor_id, v.uf
HAVING count(*) >= 20
ORDER BY pct_no_prazo DESC, pedidos_entregues DESC;
