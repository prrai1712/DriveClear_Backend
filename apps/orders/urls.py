from django.urls import path

from apps.orders.views import CreateOrderView, MyOrdersView, OrderDetailView, PreviewCheckoutView

urlpatterns = [
    path("", MyOrdersView.as_view(), name="orders-list"),
    path("preview/", PreviewCheckoutView.as_view(), name="orders-preview"),
    path("create/", CreateOrderView.as_view(), name="orders-create"),
    path("<uuid:order_uuid>/", OrderDetailView.as_view(), name="orders-detail"),
]
