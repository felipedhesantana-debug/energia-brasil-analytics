-- Fato diário: reservatórios, afluência e o preço médio do dia.
select
    h.subsistema_id,
    h.data,
    h.ear_pct,
    h.ear_mwmes,
    h.ena_pct_mlt,
    avg(f.cmo)                        as cmo_medio_dia,
    sum(f.ger_termica) / nullif(sum(f.ger_total), 0) as participacao_termica
from {{ ref('int_hidrologia_diaria') }} h
left join {{ ref('fct_energia_horaria') }} f using (subsistema_id, data)
group by all
