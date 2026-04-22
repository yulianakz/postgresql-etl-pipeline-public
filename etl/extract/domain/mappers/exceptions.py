class MapperError(Exception):
    def __init__(self, value, expected_type: str, original_error: Exception, row: dict| None = None):
        self.value = value
        self.expected_type = expected_type
        self.original_error = original_error
        self.row = row
        msg = f"Cannot convert {value!r} to {expected_type}: {original_error}"
        super().__init__(msg)