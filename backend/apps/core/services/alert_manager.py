from .notification import NotificationService


class AlertManager:
    def __init__(self):
        self.notifications = NotificationService()

    def active(self, user):
        return self.notifications.active_alerts(user)
