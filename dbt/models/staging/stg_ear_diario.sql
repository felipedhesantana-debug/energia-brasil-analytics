select
    id_subsistema                         as subsistema_id,
    cast(ear_data as date)                as data,
    ear_max_subsistema                    as ear_max_mwmes,
    ear_verif_subsistema_mwmes            as ear_mwmes,
    ear_verif_subsistema_percentual       as ear_pct
from {{ source('silver', 'ear_diario') }}
