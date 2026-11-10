-- Correlação direta entre o desvio do prazo prometido e a nota do cliente
-- Grão: uma faixa de pontualidade.
WITH avaliacao_pedido AS (
    SELECT
        pedido_id,
        avg(nota) AS nota
    FROM refined.avaliacoes
    GROUP BY pedido_id
),
desvio_entrega AS (
    SELECT
        p.pedido_id,
        date_diff('day', p.data_entrega::DATE, p.data_entrega_prevista) AS dias_antecipacao,
        CASE
            WHEN date_diff('day', p.data_entrega::DATE, p.data_entrega_prevista) >= 5 THEN '1. Antecipado (+5 dias)'
            WHEN date_diff('day', p.data_entrega::DATE, p.data_entrega_prevista) BETWEEN 1 AND 4 THEN '2. Antecipado (1 a 4 dias)'
            WHEN date_diff('day', p.data_entrega::DATE, p.data_entrega_prevista) = 0 THEN '3. No dia previsto'
            WHEN date_diff('day', p.data_entrega::DATE, p.data_entrega_prevista) BETWEEN -3 AND -1 THEN '4. Atraso leve (1 a 3 dias)'
            ELSE '5. Atraso crítico (+3 dias)'
        END AS faixa_pontualidade,
        CASE
            WHEN date_diff('day', p.data_entrega::DATE, p.data_entrega_prevista) >= 5 THEN 1
            WHEN date_diff('day', p.data_entrega::DATE, p.data_entrega_prevista) BETWEEN 1 AND 4 THEN 2
            WHEN date_diff('day', p.data_entrega::DATE, p.data_entrega_prevista) = 0 THEN 3
            WHEN date_diff('day', p.data_entrega::DATE, p.data_entrega_prevista) BETWEEN -3 AND -1 THEN 4
            ELSE 5
        END AS ordem
    FROM refined.pedidos p
    WHERE p.status = 'delivered'
      AND p.data_entrega IS NOT NULL
)
SELECT
    d.ordem,
    d.faixa_pontualidade,
    count(a.pedido_id) AS pedidos_avaliados,
    round(avg(a.nota), 2) AS nota_media,
    round(100.0 * count(*) FILTER (WHERE a.nota <= 2) / count(a.pedido_id), 1) AS pct_nota_baixa
FROM desvio_entrega d
JOIN avaliacao_pedido a ON a.pedido_id = d.pedido_id
GROUP BY d.ordem, d.faixa_pontualidade
ORDER BY d.ordem ASC;

