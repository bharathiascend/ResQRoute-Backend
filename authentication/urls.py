from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    HealthCheckView,
    RegisterView,
    LoginView,
    UserProfileView,
)

urlpatterns = [
    # Health check
    path('health/', HealthCheckView.as_view(), name='health-check-api'),
    
    # Auth endpoints
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/me/', UserProfileView.as_view(), name='user-profile'),
]
