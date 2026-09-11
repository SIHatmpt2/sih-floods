from rest_framework import serializers


class WeatherCoordinateQuerySerializer(serializers.Serializer):
    lat = serializers.FloatField(min_value=-90, max_value=90)
    lon = serializers.FloatField(min_value=-180, max_value=180)


class WeatherHistoryQuerySerializer(WeatherCoordinateQuerySerializer):
    days = serializers.IntegerField(min_value=1, max_value=365, default=7)


class WeatherCurrentSerializer(serializers.Serializer):
    station = serializers.DictField(allow_null=True)
    observed_at = serializers.DateTimeField(allow_null=True)
    temperature_c = serializers.FloatField(allow_null=True)
    rainfall_mm = serializers.FloatField(allow_null=True)
    rainfall_24h_mm = serializers.FloatField(allow_null=True)
    humidity = serializers.FloatField(allow_null=True)
    water_level_m = serializers.FloatField(allow_null=True)
    discharge_m3s = serializers.FloatField(allow_null=True)
    data_quality = serializers.DictField()


class WeatherHistoryItemSerializer(serializers.Serializer):
    observed_at = serializers.DateTimeField()
    rainfall_mm = serializers.FloatField(allow_null=True)
    temperature_c = serializers.FloatField(allow_null=True)
    humidity = serializers.FloatField(allow_null=True)
    water_level_m = serializers.FloatField(allow_null=True)
    discharge_m3s = serializers.FloatField(allow_null=True)
