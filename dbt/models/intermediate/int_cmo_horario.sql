-- O CMO é publicado a cada 30 min; o balanço é horário. Média das duas meias-horas.
select
    subsistema_id,
    date_trunc('hour', data_hora)     as data_hora,
    avg(cmo)                          as cmo,
    bool_or(flag_cmo_negativo)        as teve_cmo_negativo,
    bool_or(flag_cmo_outlier)         as teve_cmo_outlier
from {{ ref('stg_cmo_semihorario') }}
group by 1, 2
