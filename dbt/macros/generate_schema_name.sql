{#- Usa o nome do schema exatamente como configurado (staging, intermediate, gold)
    em vez do padrão do dbt "<schema_do_target>_<schema>". -#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {{ custom_schema_name if custom_schema_name is not none else target.schema }}
{%- endmacro %}
