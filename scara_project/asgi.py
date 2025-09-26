# scara_project/asgi.py

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
import scara_app.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scara_project.settings')

# Configuração final que direciona o tráfego.
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter(
            scara_app.routing.websocket_urlpatterns
        ),
})
