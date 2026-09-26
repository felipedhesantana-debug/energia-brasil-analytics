select subsistema_id, subsistema, ordem from {{ ref('subsistemas') }}
