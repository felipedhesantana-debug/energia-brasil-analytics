-- Falha se houver mais de uma linha para o mesmo subsistema e hora.
select subsistema_id, data_hora, count(*) as n
from {{ ref('fct_energia_horaria') }}
group by 1, 2
having count(*) > 1
