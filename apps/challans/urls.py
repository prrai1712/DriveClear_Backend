from django.urls import path

from apps.challans.views import FetchChallansView, ListChallansView

urlpatterns = [
    path("fetch/", FetchChallansView.as_view(), name="challan-fetch"),
    path("", ListChallansView.as_view(), name="challan-list"),
]
