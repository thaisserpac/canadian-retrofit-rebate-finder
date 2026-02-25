def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_list_all_rebates(client):
    res = client.get("/api/rebates?active_only=false")
    data = res.json()
    assert res.status_code == 200
    assert data["count"] > 0
    assert len(data["rebates"]) == data["count"]


def test_list_active_rebates(client):
    res = client.get("/api/rebates")
    data = res.json()
    assert res.status_code == 200
    for r in data["rebates"]:
        assert r["is_active"] is True


def test_filter_by_province(client):
    res = client.get("/api/rebates?province=ON")
    data = res.json()
    assert res.status_code == 200
    for r in data["rebates"]:
        assert r["province"] in ("ON", "FED")


def test_filter_bc(client):
    res = client.get("/api/rebates?province=BC")
    data = res.json()
    assert res.status_code == 200
    provinces = {r["province"] for r in data["rebates"]}
    assert "BC" in provinces


def test_search_by_retrofit_type(client):
    res = client.get("/api/rebates/search?province=ON&retrofit_type=heat_pump_air_source")
    data = res.json()
    assert res.status_code == 200
    assert data["count"] > 0


def test_search_requires_province(client):
    res = client.get("/api/rebates/search")
    assert res.status_code == 422  # Missing required param


def test_list_provinces(client):
    res = client.get("/api/rebates/provinces")
    data = res.json()
    assert res.status_code == 200
    codes = [p["code"] for p in data["provinces"]]
    assert "ON" in codes or "FED" in codes
    for p in data["provinces"]:
        assert p["program_count"] > 0
