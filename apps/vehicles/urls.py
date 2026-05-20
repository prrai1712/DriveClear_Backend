from django.urls import path

from apps.vehicles.views import RecentVehiclesView

urlpatterns = [
    path("recent/", RecentVehiclesView.as_view(), name="vehicles-recent"),
]
