-- Fato no grão subsistema x hora: geração por fonte, carga, intercâmbio e preço (CMO).
select
    b.subsistema_id,
    b.data_hora,
    cast(b.data_hora as date)                                         as data,
    hour(b.data_hora)                                                 as hora,
    b.ger_hidraulica,
    b.ger_termica,
    b.ger_eolica,
    b.ger_solar,
    b.ger_hidraulica + b.ger_termica + b.ger_eolica + b.ger_solar     as ger_total,
    b.ger_hidraulica + b.ger_eolica + b.ger_solar                     as ger_renovavel,
    b.carga,
    b.intercambio,
    c.cmo,
    coalesce(c.teve_cmo_negativo, false)                              as teve_cmo_negativo
from {{ ref('stg_balanco_horario') }} b
left join {{ ref('int_cmo_horario') }} c using (subsistema_id, data_hora)
