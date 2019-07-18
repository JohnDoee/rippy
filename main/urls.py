from django.conf import settings
from django.contrib import admin
from django.urls import path, include


urlpatterns = [path("admin/", admin.site.urls), path("api/", include("rippy.urls"))]

if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
