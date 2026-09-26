select
    id_subsistema          as subsistema_id,
    din_instante           as data_hora,
    val_cmo                as cmo,
    flag_cmo_outlier,
    flag_cmo_negativo
from {{ source('silver', 'cmo_semihorario') }}
