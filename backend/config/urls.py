from django.contrib import admin
from django.urls import path, include

from config.health import health_check


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls')),
    path('api/rooms/', include('apps.rooms.urls')),
    path('api/messages/', include('apps.messages.urls')),
    path('api/health/', health_check, name='health-check'),
]