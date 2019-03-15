from django.urls import path
from rest_framework import routers

from .views import JobViewSet, ConfigView


urlpatterns = [
    path('config/', ConfigView.as_view()),

]

router = routers.SimpleRouter()
router.register(r'jobs', JobViewSet)
urlpatterns += router.urls
