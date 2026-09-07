from rest_framework.exceptions import APIException


class WeatherServiceUnavailable(APIException):
    status_code = 503
    default_detail = "Weather service is temporarily unavailable."
    default_code = "weather_service_unavailable"


def weather_exception_handler(exc, context):
    from rest_framework.views import exception_handler

    return exception_handler(exc, context)
