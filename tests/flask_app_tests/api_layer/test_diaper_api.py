"""HTTP-level tests for the diaper-data blueprint."""

from datetime import datetime, timezone

from flask_app.domain.entities.diaper import Diaper


def _diaper(diaper_id: int = 1, baby_id: int = 1, status: str = "wet") -> Diaper:
    return Diaper(
        diaper_id=diaper_id,
        change_time=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
        status=status,
        baby_id=baby_id,
    )


class TestDiaperList:
    def test_list_requires_auth(self, client, mock_services):
        resp = client.get("/baby/1/diaper")
        assert resp.status_code == 401

    def test_list_happy_path(self, client, guest_headers, mock_services):
        mock_services["diaper"].get_diaper_by_baby_id.return_value = [
            _diaper(1), _diaper(2, status="dirty")
        ]
        resp = client.get("/baby/1/diaper", headers=guest_headers)
        assert resp.status_code == 200
        assert len(resp.get_json()) == 2

    def test_list_service_rejection_returns_400(self, client, guest_headers, mock_services):
        mock_services["diaper"].get_diaper_by_baby_id.side_effect = ValueError(
            "Invalid baby id"
        )
        resp = client.get("/baby/1/diaper", headers=guest_headers)
        assert resp.status_code == 400

    def test_create_happy_path(self, client, admin_headers, mock_services):
        mock_services["diaper"].create_diaper.return_value = _diaper()

        resp = client.post(
            "/baby/1/diaper",
            json={"change_time": "2026-01-01T10:00:00+00:00", "status": "wet"},
            headers=admin_headers,
        )

        assert resp.status_code == 201
        assert resp.get_json()["status"] == "wet"

    def test_create_invalid_status_bubbles_as_400(self, client, admin_headers, mock_services):
        mock_services["diaper"].create_diaper.side_effect = ValueError(
            "Invalid diaper status"
        )

        resp = client.post(
            "/baby/1/diaper",
            json={"change_time": "2026-01-01T10:00:00+00:00", "status": "golden"},
            headers=admin_headers,
        )

        assert resp.status_code == 400

    def test_create_invalid_payload_returns_422(self, client, admin_headers, mock_services):
        resp = client.post(
            "/baby/1/diaper",
            json={"change_time": "not-a-date", "status": "wet"},
            headers=admin_headers,
        )
        assert resp.status_code == 422
        mock_services["diaper"].create_diaper.assert_not_called()

    def test_create_requires_admin(self, client, guest_headers, mock_services):
        resp = client.post(
            "/baby/1/diaper",
            json={"change_time": "2026-01-01T10:00:00+00:00", "status": "wet"},
            headers=guest_headers,
        )
        assert resp.status_code == 403


class TestDiaperItem:
    def test_get_happy_path(self, client, guest_headers, mock_services):
        mock_services["diaper"].get_diaper_by_diaper_id.return_value = _diaper()

        resp = client.get("/baby/1/diaper/1", headers=guest_headers)
        assert resp.status_code == 200

    def test_get_returns_404(self, client, guest_headers, mock_services):
        mock_services["diaper"].get_diaper_by_diaper_id.return_value = None
        resp = client.get("/baby/1/diaper/1", headers=guest_headers)
        assert resp.status_code == 404

    def test_get_permission_error_returns_403(self, client, guest_headers, mock_services):
        mock_services["diaper"].get_diaper_by_diaper_id.side_effect = PermissionError(
            "Diaper does not belong to this baby"
        )
        resp = client.get("/baby/1/diaper/1", headers=guest_headers)
        assert resp.status_code == 403

    def test_update_happy_path(self, client, admin_headers, mock_services):
        mock_services["diaper"].update_diaper.return_value = _diaper(status="mixed")

        resp = client.put(
            "/baby/1/diaper/1",
            json={"change_time": "2026-01-01T10:00:00+00:00", "status": "mixed"},
            headers=admin_headers,
        )
        assert resp.status_code == 200

    def test_update_returns_404(self, client, admin_headers, mock_services):
        mock_services["diaper"].update_diaper.return_value = None
        resp = client.put(
            "/baby/1/diaper/99",
            json={"change_time": "2026-01-01T10:00:00+00:00", "status": "wet"},
            headers=admin_headers,
        )
        assert resp.status_code == 404

    def test_delete_happy_path(self, client, admin_headers, mock_services):
        mock_services["diaper"].delete_diaper_by_id.return_value = _diaper()
        resp = client.delete("/baby/1/diaper/1", headers=admin_headers)
        assert resp.status_code == 200
        mock_services["diaper"].delete_diaper_by_id.assert_called_once_with(1, 1)

    def test_delete_returns_404(self, client, admin_headers, mock_services):
        mock_services["diaper"].delete_diaper_by_id.return_value = None
        resp = client.delete("/baby/1/diaper/1", headers=admin_headers)
        assert resp.status_code == 404

    def test_delete_requires_admin(self, client, guest_headers, mock_services):
        resp = client.delete("/baby/1/diaper/1", headers=guest_headers)
        assert resp.status_code == 403
