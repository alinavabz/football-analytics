from football_analytics.bench import scans


def test_scans_lists_every_table_access_in_plan_order():
    plan = {
        "Node Type": "Nested Loop",
        "Plans": [
            {"Node Type": "Seq Scan", "Relation Name": "teams"},
            {"Node Type": "Index Scan", "Index Name": "events_pkey", "Relation Name": "events"},
        ],
    }
    assert scans(plan) == ["Seq Scan on teams", "Index Scan using events_pkey on events"]
