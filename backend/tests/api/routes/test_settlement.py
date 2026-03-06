from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings


def test_list_all_worklogs(client: TestClient, db: Session) -> None:
    response = client.get(f"{settings.API_V1_STR}/settlement/list-all-worklogs")
    assert response.status_code == 200
    content = response.json()
    assert "data" in content
    assert "cnt" in content
    assert isinstance(content["data"], list)
    assert isinstance(content["cnt"], int)
    assert content["cnt"] == len(content["data"])


def test_list_all_worklogs_response_structure(client: TestClient, db: Session) -> None:
    response = client.get(f"{settings.API_V1_STR}/settlement/list-all-worklogs")
    assert response.status_code == 200
    content = response.json()
    assert content["cnt"] > 0

    wl = content["data"][0]
    assert "id" in wl
    assert "user_id" in wl
    assert "task_name" in wl
    assert "desc" in wl
    assert "amt" in wl
    assert "rmtnc_sts" in wl
    assert "segments" in wl
    assert "adjustments" in wl
    assert "created_at" in wl
    assert isinstance(wl["segments"], list)
    assert isinstance(wl["adjustments"], list)


def test_list_all_worklogs_segment_structure(
    client: TestClient, db: Session
) -> None:
    response = client.get(f"{settings.API_V1_STR}/settlement/list-all-worklogs")
    assert response.status_code == 200
    content = response.json()

    wl_with_segs = next(
        (w for w in content["data"] if len(w["segments"]) > 0), None
    )
    assert wl_with_segs is not None

    seg = wl_with_segs["segments"][0]
    assert "id" in seg
    assert "hrs" in seg
    assert "rt" in seg
    assert "amt" in seg
    assert "desc" in seg
    assert "created_at" in seg


def test_list_all_worklogs_adjustment_structure(
    client: TestClient, db: Session
) -> None:
    response = client.get(f"{settings.API_V1_STR}/settlement/list-all-worklogs")
    assert response.status_code == 200
    content = response.json()

    wl_with_adjs = next(
        (w for w in content["data"] if len(w["adjustments"]) > 0), None
    )
    assert wl_with_adjs is not None

    adj = wl_with_adjs["adjustments"][0]
    assert "id" in adj
    assert "amt" in adj
    assert "rsn" in adj
    assert "created_at" in adj


def test_list_all_worklogs_filter_remitted(
    client: TestClient, db: Session
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/settlement/list-all-worklogs",
        params={"remittanceStatus": "REMITTED"},
    )
    assert response.status_code == 200
    content = response.json()
    assert isinstance(content["data"], list)
    for wl in content["data"]:
        assert wl["rmtnc_sts"] == "REMITTED"


def test_list_all_worklogs_filter_unremitted(
    client: TestClient, db: Session
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/settlement/list-all-worklogs",
        params={"remittanceStatus": "UNREMITTED"},
    )
    assert response.status_code == 200
    content = response.json()
    assert isinstance(content["data"], list)
    for wl in content["data"]:
        assert wl["rmtnc_sts"] == "UNREMITTED"


def test_list_all_worklogs_remitted_plus_unremitted_equals_total(
    client: TestClient, db: Session
) -> None:
    all_resp = client.get(f"{settings.API_V1_STR}/settlement/list-all-worklogs")
    rem_resp = client.get(
        f"{settings.API_V1_STR}/settlement/list-all-worklogs",
        params={"remittanceStatus": "REMITTED"},
    )
    unrem_resp = client.get(
        f"{settings.API_V1_STR}/settlement/list-all-worklogs",
        params={"remittanceStatus": "UNREMITTED"},
    )
    assert all_resp.status_code == 200
    assert rem_resp.status_code == 200
    assert unrem_resp.status_code == 200

    total = all_resp.json()["cnt"]
    remitted = rem_resp.json()["cnt"]
    unremitted = unrem_resp.json()["cnt"]
    assert remitted + unremitted == total


def test_generate_remittances(client: TestClient, db: Session) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/settlement/generate-remittances-for-all-users"
    )
    assert response.status_code == 200
    content = response.json()
    assert "msg" in content
    assert "cnt" in content
    assert "remittances" in content
    assert isinstance(content["remittances"], list)
    assert isinstance(content["cnt"], int)
    assert content["cnt"] == len(content["remittances"])


def test_generate_remittances_response_structure(
    client: TestClient, db: Session
) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/settlement/generate-remittances-for-all-users"
    )
    assert response.status_code == 200
    content = response.json()

    if content["cnt"] > 0:
        rmtnc = content["remittances"][0]
        assert "id" in rmtnc
        assert "user_id" in rmtnc
        assert "ttl_amt" in rmtnc
        assert "sts" in rmtnc
        assert "created_at" in rmtnc
        assert rmtnc["sts"] == "PENDING"


def test_generate_remittances_idempotent(
    client: TestClient, db: Session
) -> None:
    client.post(
        f"{settings.API_V1_STR}/settlement/generate-remittances-for-all-users"
    )
    response = client.post(
        f"{settings.API_V1_STR}/settlement/generate-remittances-for-all-users"
    )
    assert response.status_code == 200
    content = response.json()
    assert content["cnt"] == 0
    assert content["remittances"] == []
