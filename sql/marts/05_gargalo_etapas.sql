-- Decomposição do tempo total de entrega entre Despacho e Trânsito
-- Grão: uma etapa operacional da entrega.
WITH tempos AS (
    SELECT
        date_diff('hour', data_aprovacao, data_envio_transportadora) / 24.0 AS dias_despacho,
        date_diff('hour', data_envio_transportadora, data_entrega) / 24.0 AS dias_transporte
    FROM refined.pedidos
    WHERE status = 'delivered'
      AND data_aprovacao IS NOT NULL
      AND data_envio_transportadora IS NOT NULL
      AND data_entrega IS NOT NULL
      AND data_envio_transportadora >= data_aprovacao
      AND data_entrega >= data_envio_transportadora
)
SELECT
    1 AS ordem,
    '1. Despacho (Aprovação até Envio)' AS etapa,
    round(avg(dias_despacho), 1) AS dias_medio,
    round(median(dias_despacho), 1) AS dias_mediana
FROM tempos
UNION ALL
SELECT
    2 AS ordem,
    '2. Trânsito (Transportadora até Cliente)' AS etapa,
    round(avg(dias_transporte), 1) AS dias_medio,
    round(median(dias_transporte), 1) AS dias_mediana
FROM tempos
ORDER BY ordem ASC;

