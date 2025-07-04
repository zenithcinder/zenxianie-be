from django.apps import AppConfig


class JwtBlacklistConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.api.jwt_blacklist"

    def ready(self):
        import app.api.jwt_blacklist.signals  # noqa
