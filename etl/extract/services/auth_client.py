import requests

from etl.extract.services.exceptions import AuthError


class ApiAuthClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.token = None

    def login(self):
        url = f"{self.base_url}/auth/login"
        response = requests.post(
            url,
            json={
                "user_name": self.username,
                "password": self.password
            }
        )
        try:
            response.raise_for_status()
            self.token = response.json()["access_token"]
        except requests.HTTPError as e:
            raise AuthError(url=url, status_code=response.status_code, original_error=e)
        except (KeyError, ValueError) as e:
            raise AuthError(url=url, status_code=response.status_code, original_error=e)

    @property
    def headers(self):
        if not self.token:
            raise AuthError(url=self.base_url, status_code=None, original_error=None)
        return {
            "Authorization": f"Bearer {self.token}"
        }
