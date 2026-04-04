from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls')),
    path('api/rooms/', include('apps.rooms.urls')),
    path('api/messages/', include('apps.messages.urls')),
]