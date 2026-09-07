from rest_framework.exceptions import APIException


class RiskServiceUnavailable(APIException):
    status_code = 503
    default_detail = "Risk service is temporarily unavailable."
    default_code = "risk_service_unavailable"
