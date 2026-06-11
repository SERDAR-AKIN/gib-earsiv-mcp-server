class GibMcpError(Exception):
    pass

class AuthenticationError(GibMcpError):
    pass

class GibApiError(GibMcpError):
    def __init__(self, message: str, status_code: int = None, response_text: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text

class SessionExpiredError(GibMcpError):
    pass

class ParameterFormattingError(GibMcpError):
    pass
