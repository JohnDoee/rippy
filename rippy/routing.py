from django.urls import path

from .consumers import EventConsumer

urlpatterns = [path("events/", EventConsumer)]
