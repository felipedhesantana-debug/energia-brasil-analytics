select
    e.subsistema_id,
    e.data,
    e.ear_pct,
    e.ear_mwmes,
    e.ear_max_mwmes,
    n.ena_pct_mlt,
    n.ena_mwmed
from {{ ref('stg_ear_diario') }} e
left join {{ ref('stg_ena_diario') }} n using (subsistema_id, data)
