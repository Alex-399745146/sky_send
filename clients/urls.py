# clients/urls.py

from django.urls import path

from .views import (
    home,
    ClientListView,
    ClientDetailView,
    ClientCreateView,
    ClientUpdateView,
    ClientDeleteView,
)

app_name = "clients"

urlpatterns = [
    path("", home, name="home"),
    path("clients/", ClientListView.as_view(), name="client_list"),
    path("clients/create/", ClientCreateView.as_view(), name="client_create"),
    path("clients/<int:pk>/", ClientDetailView.as_view(), name="client_detail"),
    path("clients/<int:pk>/edit/", ClientUpdateView.as_view(), name="client_edit"),
    path("clients/<int:pk>/delete/", ClientDeleteView.as_view(), name="client_delete"),
]
