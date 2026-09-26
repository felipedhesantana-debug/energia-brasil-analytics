-- =====================================================================
-- Energia no Brasil — análises de negócio em SQL (DuckDB)
-- Abra data/energia.duckdb no DBeaver e rode bloco a bloco.
-- Referência de preço: CMO do Sudeste/Centro-Oeste (maior submercado).
-- =====================================================================


-- 1) Resumo por ano: preço, matriz e reservatórios
select * from gold.mart_resumo_anual order by ano;


-- 2) Preço médio por hora do dia no ano atual (a "curva do pato":
--    a solar derruba o preço ao meio-dia e ele volta a subir no fim da tarde)
select
    hora,
    round(avg(cmo), 0)                         as cmo_medio,
    round(avg(ger_solar) / 1000, 1)            as solar_gw_se
from gold.mart_energia_dashboard
where subsistema_id = 'SE'
  and ano = (select max(ano) from gold.mart_energia_dashboard)
group by hora
order by hora;


-- 3) Quando o reservatório esvazia, o preço dispara? (faixas de EAR no SE/CO)
select
    faixa_reservatorio,
    count(distinct data)                                   as dias,
    round(avg(cmo), 0)                                     as cmo_medio,
    round(100 * sum(ger_termica) / sum(ger_total), 1)      as pct_termica
from gold.mart_energia_dashboard
where subsistema_id = 'SE'
group by 1
order by 1;


-- 4) Correlação entre reservatório e preço (médias mensais do SE/CO)
with mensal as (
    select inicio_mes, avg(ear_pct) as ear, avg(cmo) as cmo
    from gold.mart_energia_dashboard
    where subsistema_id = 'SE'
    group by 1
)
select round(corr(ear, cmo), 2) as correlacao_ear_cmo, count(*) as meses
from mensal;


-- 5) Horas de energia "de graça" (CMO < R$ 1) e de preço extremo (>= R$ 500) por ano e subsistema
select
    ano,
    subsistema,
    round(100 * avg(hora_cmo_zero), 1)       as pct_horas_cmo_zero,
    sum(hora_cmo_acima_500)                   as horas_cmo_acima_500
from gold.mart_energia_dashboard
group by 1, 2
order by 1, 2;


-- 6) Crescimento da solar e da eólica (TWh por ano, Brasil)
select
    ano,
    fonte,
    round(sum(energia_twh), 1) as twh,
    round(100 * sum(energia_twh) / sum(sum(energia_twh)) over (partition by ano), 1) as participacao_pct
from gold.mart_matriz_perfil
group by 1, 2
order by 1, 2;


-- 7) Descolamento de preço entre submercados (spread médio vs. SE/CO, por ano)
with p as (
    select ano, subsistema_id, avg(cmo) as cmo
    from gold.mart_energia_dashboard
    group by 1, 2
)
select
    p.ano,
    p.subsistema_id,
    round(p.cmo, 0)                        as cmo_medio,
    round(p.cmo - se.cmo, 0)               as spread_vs_se
from p
join p se on se.ano = p.ano and se.subsistema_id = 'SE'
order by 1, 2;


-- 8) Período seco (mai–nov) x úmido (dez–abr): preço e térmicas
select
    ano,
    periodo_hidrologico,
    round(avg(case when subsistema_id = 'SE' then cmo end), 0)  as cmo_medio_se,
    round(100 * sum(ger_termica) / sum(ger_total), 1)           as pct_termica
from gold.mart_energia_dashboard
group by 1, 2
order by 1, 2;


-- 9) Os 10 dias mais caros da série (SE/CO) e o que estava acontecendo
select
    data,
    round(avg(cmo), 0)                                  as cmo_medio_dia,
    round(avg(ear_pct), 1)                              as reservatorio_pct,
    round(avg(ena_pct_mlt), 1)                          as chuva_pct_media,
    round(100 * sum(ger_termica) / sum(ger_total), 1)   as pct_termica
from gold.mart_energia_dashboard
where subsistema_id = 'SE'
group by data
order by cmo_medio_dia desc
limit 10;


-- 10) Carga (consumo) média por hora: quando o Brasil mais consome energia
select
    hora,
    round(sum(carga) / count(distinct data_hora) / 1000, 1) as carga_gw
from gold.mart_energia_dashboard
where ano = (select max(ano) from gold.mart_energia_dashboard)
group by hora
order by hora;
