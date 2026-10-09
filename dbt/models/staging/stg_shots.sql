select
    event_id as shot_id,
    xg,
    outcome,
    outcome = 'Goal' as is_goal,
    body_part,
    technique,
    shot_type,
    end_x,
    end_y,
    first_time,
    key_pass_id
from {{ source('core', 'shots') }}
