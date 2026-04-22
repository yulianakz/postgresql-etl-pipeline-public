"""HTTP-level tests for the /baby blueprint."""

from flask_app.domain.entities.baby import Baby


def _baby(baby_id: int = 1) -> Baby:
    return Baby(baby_id=baby_id, name="Adriana", timezone="Europe/Chisinau")


class TestListAndCreate:
    def test_list_requires_auth(self, client, mock_services):
        resp = client.get("/baby/")
        assert resp.status_code == 401
        mock_services["baby"].get_all_babies.assert_not_called()

    def test_list_happy_path_any_role(self, client, guest_headers, mock_services):
        mock_services["baby"].get_all_babies.return_value = [_baby(1), _baby(2)]

        resp = client.get("/baby/", headers=guest_headers)

        assert resp.status_code == 200
        body = resp.get_json()
        assert len(body) == 2
        assert body[0]["name"] == "Adriana"

    def test_create_requires_admin(self, client, guest_headers, mock_services):
        resp = client.post(
            "/baby/",
            json={"name": "Adriana", "timezone": "Europe/Chisinau"},
            headers=guest_headers,
        )
        assert resp.status_code == 403
        mock_services["baby"].create_baby.assert_not_called()

    def test_create_happy_path(self, client, admin_headers, mock_services):
        mock_services["baby"].create_baby.return_value = _baby()

        resp = client.post(
            "/baby/",
            json={"name": "Adriana", "timezone": "Europe/Chisinau"},
            headers=admin_headers,
        )

        assert resp.status_code == 201
        assert resp.get_json()["name"] == "Adriana"
        mock_services["baby"].create_baby.assert_called_once_with(
            "Adriana", "Europe/Chisinau"
        )

    def test_create_unknown_field_returns_422(self, client, admin_headers, mock_services):
        resp = client.post(
            "/baby/",
            json={"name": "Adriana", "timezone": "UTC", "extra": "x"},
            headers=admin_headers,
        )
        assert resp.status_code == 422
        mock_services["baby"].create_baby.assert_not_called()

    def test_create_service_error_maps_to_400(self, client, admin_headers, mock_services):
        mock_services["baby"].create_baby.side_effect = ValueError("Invalid timezone")

        resp = client.post(
            "/baby/",
            json={"name": "Adriana", "timezone": "Mars/Phobos"},
            headers=admin_headers,
        )

        assert resp.status_code == 400
        assert "Invalid timezone" in resp.get_json()["message"]


class TestGetUpdateDelete:
    def test_get_happy_path(self, client, guest_headers, mock_services):
        mock_services["baby"].get_baby_by_id.return_value = _baby(5)

        resp = client.get("/baby/5", headers=guest_headers)

        assert resp.status_code == 200
        assert resp.get_json()["id"] == 5

    def test_get_returns_404_when_missing(self, client, guest_headers, mock_services):
        mock_services["baby"].get_baby_by_id.return_value = None

        resp = client.get("/baby/5", headers=guest_headers)

        assert resp.status_code == 404

    def test_get_value_error_returns_400(self, client, guest_headers, mock_services):
        mock_services["baby"].get_baby_by_id.side_effect = ValueError("Invalid baby id")

        resp = client.get("/baby/5", headers=guest_headers)

        assert resp.status_code == 400

    def test_update_happy_path(self, client, admin_headers, mock_services):
        mock_services["baby"].update_baby_info.return_value = _baby(5)

        resp = client.put(
            "/baby/5",
            json={"name": "Adi", "timezone": "UTC"},
            headers=admin_headers,
        )

        assert resp.status_code == 200
        mock_services["baby"].update_baby_info.assert_called_once_with(5, "Adi", "UTC")

    def test_update_returns_404(self, client, admin_headers, mock_services):
        mock_services["baby"].update_baby_info.return_value = None

        resp = client.put(
            "/baby/5",
            json={"name": "Adi", "timezone": "UTC"},
            headers=admin_headers,
        )

        assert resp.status_code == 404

    def test_update_requires_admin(self, client, guest_headers, mock_services):
        resp = client.put(
            "/baby/5",
            json={"name": "Adi", "timezone": "UTC"},
            headers=guest_headers,
        )
        assert resp.status_code == 403
        mock_services["baby"].update_baby_info.assert_not_called()

    def test_delete_happy_path(self, client, admin_headers, mock_services):
        mock_services["baby"].delete_baby_by_id.return_value = _baby(5)

        resp = client.delete("/baby/5", headers=admin_headers)

        assert resp.status_code == 200
        mock_services["baby"].delete_baby_by_id.assert_called_once_with(5)

    def test_delete_returns_404_when_missing(self, client, admin_headers, mock_services):
        mock_services["baby"].delete_baby_by_id.return_value = None

        resp = client.delete("/baby/5", headers=admin_headers)

        assert resp.status_code == 404

    def test_delete_requires_admin(self, client, guest_headers, mock_services):
        resp = client.delete("/baby/5", headers=guest_headers)
        assert resp.status_code == 403
        mock_services["baby"].delete_baby_by_id.assert_not_called()
