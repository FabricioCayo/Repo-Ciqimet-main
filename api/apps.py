from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError


class BackendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'  # Tu app se llama 'api'

    def ready(self):
        from django.contrib.auth import get_user_model
        from django.db import connection

        User = get_user_model()

        try:
            if not User.objects.filter(username='admin@example.com').exists():
                User.objects.create_user(
                    firstname='Juan',
                    lastname='Pérez',
                    username='admin@example.com',
                    password='adminsegura123',
                    rut='12.345.678-9',
                    rolname='administrador',
                    turno='Dia',
                    numero='+56912345678',
                    is_staff=True,
                    is_superuser=True
                )
                print("✅ Usuario administrador creado automáticamente")
        except (OperationalError, ProgrammingError):
            # Puede fallar si las migraciones aún no se aplican
            pass

