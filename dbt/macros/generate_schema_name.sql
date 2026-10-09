{#- Use the folder's schema name as is (staging, marts) instead of dbt's default analytics_staging. -#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {{ custom_schema_name | trim if custom_schema_name else target.schema }}
{%- endmacro %}
