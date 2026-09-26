select
    id_subsistema                          as subsistema_id,
    cast(ena_data as date)                 as data,
    ena_bruta_regiao_mwmed                 as ena_mwmed,
    ena_bruta_regiao_percentualmlt         as ena_pct_mlt
from {{ source('silver', 'ena_diario') }}
