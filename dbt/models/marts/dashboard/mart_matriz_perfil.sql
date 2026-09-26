-- Matriz elétrica do Brasil (soma dos 4 subsistemas) no formato longo: ano x mês x hora x fonte.
-- Serve para os gráficos de "geração por fonte" e "perfil horário" (curva do pato) no Tableau.
with brasil as (
    select
        data_hora,
        sum(ger_hidraulica) as hidraulica,
        sum(ger_termica)    as termica,
        sum(ger_eolica)     as eolica,
        sum(ger_solar)      as solar,
        sum(carga)          as carga
    from {{ ref('fct_energia_horaria') }}
    group by 1
),
longo as (
    unpivot brasil
    on hidraulica, solar, termica, eolica
    into name fonte_id value geracao_mwmed
)
select
    year(data_hora)                         as ano,
    month(data_hora)                        as mes,
    hour(data_hora)                         as hora,
    -- prefixo numérico: define a ordem (e as cores) no Tableau
    case fonte_id
        when 'hidraulica' then '1. Hidráulica'
        when 'solar'      then '2. Solar'
        when 'termica'    then '3. Térmica'
        when 'eolica'     then '4. Eólica'
    end                                     as fonte,
    avg(geracao_mwmed)                      as geracao_mwmed,
    sum(geracao_mwmed) / 1e6                as energia_twh,
    count(*)                                as horas
from longo
group by all
