from django.urls import path

from .views import WeatherCurrentView, WeatherHistoryView, WeatherStationListView

urlpatterns = [
    path("current/", WeatherCurrentView.as_view(), name="weather-current"),
    path("history/", WeatherHistoryView.as_view(), name="weather-history"),
    path("stations/", WeatherStationListView.as_view(), name="weather-stations"),
]
