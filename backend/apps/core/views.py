from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.services.core_service import CoreService
from .serializers import CoordinateQuerySerializer, NotificationRecordSerializer

service = CoreService()


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = CoordinateQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        data = service.dashboard(
            request.user,
            query.validated_data["lat"],
            query.validated_data["lon"],
        )
        return Response(data)


class AnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(service.analytics(request.query_params.get("state")))


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        unread = request.query_params.get("unread") == "true"
        data = NotificationRecordSerializer(
            service.notifications(request.user, unread_only=unread),
            many=True,
        ).data
        return Response(data)


class SafeZoneView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = CoordinateQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        result = service.safe_zone(
            query.validated_data["lat"],
            query.validated_data["lon"],
        )
        return Response(result or {"detail": "No suitable zone found"}, status=200 if result else 404)
