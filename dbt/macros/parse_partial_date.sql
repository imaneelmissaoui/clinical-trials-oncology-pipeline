{% macro parse_partial_date(value_expression) -%}
    case
        when {{ value_expression }} ~ '^[0-9]{4}$'
            and pg_input_is_valid({{ value_expression }} || '-01-01', 'date')
            then ({{ value_expression }} || '-01-01')::date
        when {{ value_expression }} ~ '^[0-9]{4}-[0-9]{2}$'
            and pg_input_is_valid({{ value_expression }} || '-01', 'date')
            then ({{ value_expression }} || '-01')::date
        when {{ value_expression }} ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
            and pg_input_is_valid({{ value_expression }}, 'date')
            then {{ value_expression }}::date
        else null
    end
{%- endmacro %}
