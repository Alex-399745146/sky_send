# clients/urls.py
from django.urls import path

from .views import home

app_name = "clients"

urlpatterns = [
    path("", home, name="home"),
]
