-- Após a limpeza, o CMO deve ficar entre -R$ 5.000 e R$ 5.000/MWh.
select * from {{ ref('fct_energia_horaria') }} where abs(cmo) > 5000
