-- Pelo menos 98% das horas do balanço devem ter preço (CMO) associado.
select count(*) filter (where cmo is null) as sem_cmo, count(*) as total
from {{ ref('fct_energia_horaria') }}
having count(*) filter (where cmo is null) > 0.02 * count(*)
