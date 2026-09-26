with dias as (
    select cast(d as date) as data
    from range(date '2020-01-01', current_date + 1, interval 1 day) t(d)
)
select
    data,
    year(data)                                                     as ano,
    month(data)                                                    as mes,
    ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'][month(data)] as nome_mes,
    date_trunc('month', data)                                      as inicio_mes,
    isodow(data)                                                   as dia_semana_num,
    case when month(data) between 5 and 11 then 'Seco' else 'Úmido' end as periodo_hidrologico
from dias
