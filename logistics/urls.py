from django.urls import path
from .views import (
    ShipmentListCreateView,
    ShipmentDetailView,
    TripActivateView,
    TripStatusUpdateView,
    DriverActiveTripsView,
    RouteRiskEvaluateView,
)

app_name = 'logistics'

urlpatterns = [
    # Shipments
    path('shipments/', ShipmentListCreateView.as_view(), name='shipment-list-create'),
    path('shipments/<str:code>/', ShipmentDetailView.as_view(), name='shipment-detail'),

    # Trip Activation & Execution
    path('trips/activate/', TripActivateView.as_view(), name='trip-activate'),
    path('trips/active/', DriverActiveTripsView.as_view(), name='driver-active-trips'),
    path('trips/<str:trip_code>/status/', TripStatusUpdateView.as_view(), name='trip-status-update'),

    # On-demand AI Risk Engine
    path('risk-engine/assess/', RouteRiskEvaluateView.as_view(), name='route-risk-assess'),
]
