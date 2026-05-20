from django.urls import path

from apps.support.views import CreateTicketView, ListTicketsView

urlpatterns = [
    path("", ListTicketsView.as_view(), name="support-list"),
    path("create/", CreateTicketView.as_view(), name="support-create"),
]
