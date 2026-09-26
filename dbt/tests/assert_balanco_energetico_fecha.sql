-- Física do sistema: geração = carga + intercâmbio. Aceitamos até 1% das horas fora da tolerância de 2%.
with erro as (
    select abs(ger_total - carga - intercambio) / nullif(carga, 0) as erro_rel
    from {{ ref('fct_energia_horaria') }}
)
select count(*) filter (where erro_rel > 0.02) as horas_fora, count(*) as total
from erro
having count(*) filter (where erro_rel > 0.02) > 0.01 * count(*)
