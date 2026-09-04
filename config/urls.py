from django.contrib import admin
from django.urls import path, include
from authentication.views import HealthCheckView

urlpatterns = [
    # Root path returns health & API status
    path('', HealthCheckView.as_view(), name='root-health-status'),
    path('admin/', admin.site.urls),
    
    # Root health check endpoint (SIH26002 STEP 01 requirement)
    path('health/', HealthCheckView.as_view(), name='root-health-check'),
    
    # API endpoints
    path('api/', include('authentication.urls')),
]
