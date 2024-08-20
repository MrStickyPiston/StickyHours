class ZermeloException(Exception):
    pass


class ZermeloFunctionSettingsError(ZermeloException):
    def __init__(self, setting, value, required_value, endpoint):
        super().__init__(
            f"Functionsetting {setting} was {value} but endpoint {endpoint} requires the setting to be {required_value}.")

        self.setting = setting
        self.value = value
        self.required_value = required_value
        self.endpoint = endpoint


class ZermeloValueError(ZermeloException):
    pass


class ZermeloAuthException(ZermeloException):
    pass


class ZermeloApiDataException(ZermeloException):
    pass


class ZermeloApiNetworkError(ZermeloException):
    pass


class ZermeloApiHttpStatusException(ZermeloException):
    def __init__(self, status, response):
        message = f"Zermelo api returned HTTP error {status}."

        super().__init__(message)
        self.message = message
        self.status = status
        self.response = response

    def __str__(self):
        return f"{self.message}\nHttp code: {self.status}\nBody: {self.response}"
