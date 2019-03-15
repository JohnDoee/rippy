from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path, include

import rippy.routing


application = ProtocolTypeRouter({
    'websocket': URLRouter([
        path('api/', URLRouter(rippy.routing.urlpatterns)),
    ]),
})