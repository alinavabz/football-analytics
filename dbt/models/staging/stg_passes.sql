select
    event_id as pass_id,
    recipient_player_id,
    length,
    height,
    body_part,
    pass_type,
    is_cross,
    outcome,
    outcome = 'Complete' as is_complete
from {{ source('core', 'passes') }}
