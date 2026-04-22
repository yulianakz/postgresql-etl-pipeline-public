class AuthError(Exception):
    def __init__(self, url: str, status_code: int | None, original_error: Exception | None):
        self.url = url
        self.status_code = status_code
        self.original_error = original_error
        msg = f"Authentication failed at {url}: [{status_code}] {original_error}"
        super().__init__(msg)
