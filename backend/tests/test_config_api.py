def test_get_default_config(client):
    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert data["search"]["lookback_days"] == 7
    assert data["search"]["max_results_per_source"] == 30
    assert data["delivery"]["provider"] == "feishu"
    assert data["topics"] == [
        {
            "name": "llm_agents",
            "keywords": ["LLM agent", "tool use", "autonomous agents"],
            "venues": ["ICLR", "NeurIPS", "ACL"],
            "exclude_keywords": ["survey"],
        }
    ]


def test_save_and_read_config(client):
    payload = {
        "topics": [
            {
                "name": "llm_agents",
                "keywords": ["LLM agent", "tool use"],
                "venues": ["ICLR", "NeurIPS"],
                "exclude_keywords": ["survey"],
            }
        ],
        "search": {"lookback_days": 3, "max_results_per_source": 12},
        "summary": {"language": "zh"},
        "delivery": {"provider": "feishu", "mode": "app_bot", "recipient_id_type": "email"},
    }

    put_response = client.put("/api/config", json=payload)
    assert put_response.status_code == 200
    assert put_response.json()["topics"][0]["name"] == "llm_agents"

    get_response = client.get("/api/config")
    assert get_response.status_code == 200
    assert get_response.json() == put_response.json()
