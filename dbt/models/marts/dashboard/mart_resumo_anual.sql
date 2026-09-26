-- Indicadores por ano (Brasil = soma dos subsistemas; preço = Sudeste/Centro-Oeste ponderado pela carga do SIN).
with base as (
    select * from {{ ref('mart_energia_dashboard') }}
)
select
    ano,
    round(sum(cmo * carga) / sum(carga), 2)                       as cmo_medio_ponderado,
    round(avg(case when subsistema_id = 'SE' then cmo end), 2)     as cmo_medio_se,
    round(100 * sum(ger_renovavel) / sum(ger_total), 2)           as pct_renovavel,
    round(100 * sum(ger_solar) / sum(ger_total), 2)               as pct_solar,
    round(100 * sum(ger_eolica) / sum(ger_total), 2)              as pct_eolica,
    round(100 * sum(ger_termica) / sum(ger_total), 2)             as pct_termica,
    round(100 * sum(ger_hidraulica) / sum(ger_total), 2)          as pct_hidraulica,
    round(avg(case when subsistema_id = 'SE' then ear_pct end), 2) as ear_medio_se
from base
group by ano
order by ano
