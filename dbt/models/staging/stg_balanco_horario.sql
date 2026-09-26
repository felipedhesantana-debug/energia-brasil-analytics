select
    id_subsistema                          as subsistema_id,
    din_instante                           as data_hora,
    coalesce(val_gerhidraulica, 0)         as ger_hidraulica,
    coalesce(val_gertermica, 0)            as ger_termica,
    coalesce(val_gereolica, 0)             as ger_eolica,
    coalesce(val_gersolar, 0)              as ger_solar,
    val_carga                              as carga,
    val_intercambio                        as intercambio
from {{ source('silver', 'balanco_horario') }}
where not flag_sin
