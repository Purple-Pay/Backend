SUCCESS = "SUCCESS"
FAIL = "FAIL"
UNKNOWN_ERROR = "UNKNOWN_ERROR"
INVALID_REQUEST = "INVALID_REQUEST"
INVALID_REQUEST_BODY = "INVALID_REQUEST_BODY"
INVALID_SIGNATURE = "INVALID_SIGNATURE"
INVALID_TIMESTAMP = "INVALID_TIMESTAMP"
INVALID_API_KEY = "INVALID_API_KEY"
MISSING_API_KEY = "MISSING_API_KEY"
INVALID_NONCE = "INVALID_NONCE"
MISSING_NONCE = "MISSING_NONCE"
WRONG_HTTP_METHOD = "WRONG_HTTP_METHOD"
REQUIRED_PARAM_EMPTY_OR_BAD = "REQUIRED_PARAM_EMPTY_OR_BAD"

ERROR_DETAILS = {
    UNKNOWN_ERROR: {"name": "UNKNOWN_ERROR", "code": 400000, "message": "An unknown error occurred while processing the request", "http_status": 400},
    INVALID_REQUEST: {"name": "INVALID_REQUEST", "code": 400001, "message": "Request is invalid.", "http_status": 400},
    INVALID_REQUEST_BODY: {"name": "INVALID_REQUEST_BODY", "code": 400002, "message": "Request body is not valid", "http_status": 400},
    INVALID_SIGNATURE: {"name": "INVALID_SIGNATURE", "code": 400003, "message": "Signature is invalid", "http_status": 400},
    INVALID_TIMESTAMP: {"name": "INVALID_TIMESTAMP", "code": 400004, "message": "Timestamp is invalid or outside the permisible window.", "http_status": 400},
    INVALID_API_KEY: {"name": "INVALID_API_KEY", "code": 400005, "message": "API key not found or invalid", "http_status": 400},
    MISSING_API_KEY: {"name": "MISSING_API_KEY", "code": 400006, "message": "API key is missing in the request", "http_status": 400},
    INVALID_NONCE: {"name": "INVALID_NONCE", "code": 400007, "message": "Nonce not found or invalid", "http_status": 400},
    MISSING_NONCE: {"name": "MISSING_NONCE", "code": 400008, "message": "Nonce is missing in the request", "http_status": 400},
    WRONG_HTTP_METHOD: {"name": "WRONG_HTTP_METHOD", "code": 400009, "message": "Request method is not supported", "http_status": 400},
    REQUIRED_PARAM_EMPTY_OR_BAD: {"name": "REQUIRED_PARAM_EMPTY_OR_BAD", "code": 400010, "message": "Request body is not valid", "http_status": 400},
}


API_REQUEST_STATUS_DETAILS = {
    SUCCESS: {"name": "SUCCESS", "code": 200000, "message": "Request successfully processed", "http_status": 200},
    FAIL: {"name": "FAIL", "details": ERROR_DETAILS},
}




API_STATUS_ENUM = [SUCCESS, FAIL]