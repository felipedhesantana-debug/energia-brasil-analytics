-- Base "larga" do Tableau: subsistema x hora, com calendário e hidrologia do dia.
select
    f.data_hora,
    data,
    cal.ano,
    cal.mes,
    cal.nome_mes,
    cal.inicio_mes,
    cal.periodo_hidrologico,
    f.hora,
    f.subsistema_id,
    s.subsistema,
    f.cmo,
    f.ger_hidraulica,
    f.ger_termica,
    f.ger_eolica,
    f.ger_solar,
    f.ger_total,
    f.ger_renovavel,
    f.carga,
    f.intercambio,
    h.ear_pct,
    h.ena_pct_mlt,
    case
        when h.ear_pct < 40 then '1. Abaixo de 40%'
        when h.ear_pct < 60 then '2. 40% a 60%'
        else '3. Acima de 60%'
    end                                   as faixa_reservatorio,
    case when f.cmo < 1 then 1 else 0 end   as hora_cmo_zero,
    case when f.cmo >= 500 then 1 else 0 end as hora_cmo_acima_500
from {{ ref('fct_energia_horaria') }} f
join {{ ref('dim_calendario') }} cal using (data)
join {{ ref('dim_subsistema') }} s using (subsistema_id)
left join {{ ref('int_hidrologia_diaria') }} h using (subsistema_id, data)
