-- Grain: one row per player.
-- team_id is the team the player was named in a squad for most often (one team per player in a
-- single international tournament).
with squad_team as (
    select
        player_id,
        mode() within group (order by team_id) as team_id
    from {{ ref('stg_match_players') }}
    group by player_id
)

select
    p.player_id,
    p.player_name,
    p.display_name,
    p.country_name,
    st.team_id
from {{ ref('stg_players') }} as p
left join squad_team as st using (player_id)
