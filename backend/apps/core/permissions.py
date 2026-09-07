from rest_framework.permissions import IsAuthenticated


class CorePermission(IsAuthenticated):
    pass
