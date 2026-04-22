"""HTTP-level tests for the sleep-data blueprint."""

from datetime import datetime, timezone

from flask_app.domain.entities.sleep import Sleep


def _sleep(sleep_id: int = 1, baby_id: int = 1) -> Sleep:
    return Sleep(
        sleep_id=sleep_id,
        sleep_start=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
        sleep_duration=60,
        baby_id=baby_id,
    )


class TestSleepList:
    def test_list_requires_auth(self, client, mock_services):
        resp = client.get("/baby/1/sleep")
        assert resp.status_code == 401
        mock_services["sleep"].get_sleep_by_baby_id.assert_not_called()

    def test_list_happy_path(self, client, guest_headers, mock_services):
        mock_services["sleep"].get_sleep_by_baby_id.return_value = [_sleep(1), _sleep(2)]

        resp = client.get("/baby/1/sleep", headers=guest_headers)

        assert resp.status_code == 200
        assert len(resp.get_json()) == 2

    def test_list_value_error_returns_400(self, client, guest_headers, mock_services):
        mock_services["sleep"].get_sleep_by_baby_id.side_effect = ValueError(
            "Baby id does not exist"
        )

        resp = client.get("/baby/999/sleep", headers=guest_headers)
        assert resp.status_code == 400

    def test_create_happy_path(self, client, admin_headers, mock_services):
        mock_services["sleep"].create_sleep.return_value = _sleep()

        resp = client.post(
            "/baby/1/sleep",
            json={
                "sleep_start": "2026-01-01T10:00:00+00:00",
                "sleep_duration": 60,
            },
            headers=admin_headers,
        )

        assert resp.status_code == 201
        mock_services["sleep"].create_sleep.assert_called_once()

    def test_create_requires_admin(self, client, guest_headers, mock_services):
        resp = client.post(
            "/baby/1/sleep",
            json={
                "sleep_start": "2026-01-01T10:00:00+00:00",
                "sleep_duration": 60,
            },
            headers=guest_headers,
        )
        assert resp.status_code == 403
        mock_services["sleep"].create_sleep.assert_not_called()

    def test_create_invalid_payload_returns_422(self, client, admin_headers, mock_services):
        resp = client.post(
            "/baby/1/sleep",
            json={"sleep_start": "not-a-date", "sleep_duration": 60},
            headers=admin_headers,
        )
        assert resp.status_code == 422
        mock_services["sleep"].create_sleep.assert_not_called()

    def test_create_unknown_field_returns_422(self, client, admin_headers, mock_services):
        resp = client.post(
            "/baby/1/sleep",
            json={
                "sleep_start": "2026-01-01T10:00:00+00:00",
                "sleep_duration": 60,
                "extra": "x",
            },
            headers=admin_headers,
        )
        assert resp.status_code == 422
        mock_services["sleep"].create_sleep.assert_not_called()

    def test_create_service_rejection_maps_to_400(self, client, admin_headers, mock_services):
        mock_services["sleep"].create_sleep.side_effect = ValueError("future")

        resp = client.post(
            "/baby/1/sleep",
            json={
                "sleep_start": "2026-01-01T10:00:00+00:00",
                "sleep_duration": 60,
            },
            headers=admin_headers,
        )

        assert resp.status_code == 400


class TestSleepItem:
    def test_get_happy_path(self, client, guest_headers, mock_services):
        mock_services["sleep"].get_sleep_by_sleep_id.return_value = _sleep()

        resp = client.get("/baby/1/sleep/1", headers=guest_headers)

        assert resp.status_code == 200

    def test_get_returns_404(self, client, guest_headers, mock_services):
        mock_services["sleep"].get_sleep_by_sleep_id.return_value = None
        resp = client.get("/baby/1/sleep/9", headers=guest_headers)
        assert resp.status_code == 404

    def test_get_permission_error_returns_403(self, client, guest_headers, mock_services):
        mock_services["sleep"].get_sleep_by_sleep_id.side_effect = PermissionError(
            "Sleep does not belong to this baby"
        )

        resp = client.get("/baby/1/sleep/9", headers=guest_headers)
        assert resp.status_code == 403

    def test_update_happy_path(self, client, admin_headers, mock_services):
        mock_services["sleep"].update_sleep.return_value = _sleep()

        resp = client.put(
            "/baby/1/sleep/1",
            json={
                "sleep_start": "2026-01-01T10:00:00+00:00",
                "sleep_duration": 90,
            },
            headers=admin_headers,
        )

        assert resp.status_code == 200

    def test_update_returns_404(self, client, admin_headers, mock_services):
        mock_services["sleep"].update_sleep.return_value = None

        resp = client.put(
            "/baby/1/sleep/99",
            json={
                "sleep_start": "2026-01-01T10:00:00+00:00",
                "sleep_duration": 90,
            },
            headers=admin_headers,
        )

        assert resp.status_code == 404

    def test_delete_happy_path(self, client, admin_headers, mock_services):
        mock_services["sleep"].delete_sleep_by_id.return_value = _sleep()

        resp = client.delete("/baby/1/sleep/1", headers=admin_headers)

        assert resp.status_code == 200
        mock_services["sleep"].delete_sleep_by_id.assert_called_once_with(1, 1)

    def test_delete_returns_404(self, client, admin_headers, mock_services):
        mock_services["sleep"].delete_sleep_by_id.return_value = None
        resp = client.delete("/baby/1/sleep/1", headers=admin_headers)
        assert resp.status_code == 404

    def test_delete_requires_admin(self, client, guest_headers, mock_services):
        resp = client.delete("/baby/1/sleep/1", headers=guest_headers)
        assert resp.status_code == 403
        mock_services["sleep"].delete_sleep_by_id.assert_not_called()
