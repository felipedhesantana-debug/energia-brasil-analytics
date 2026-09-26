select * from {{ ref('fct_hidrologia_diaria') }} where ear_pct < 0 or ear_pct > 100
