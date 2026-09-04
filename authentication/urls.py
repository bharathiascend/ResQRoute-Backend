from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    HealthCheckView,
    RegisterView,
    LoginView,
    UserProfileView,
    AuthorityRequestListView,
    AuthorityApprovalView,
    RerouteReportsView,
    ForgotPasswordView,
    ChangePasswordView,
    OfficialResetRequestsListView,
    OfficialResetActionView,
)

urlpatterns = [
    # Health check
    path('health/', HealthCheckView.as_view(), name='health-check-api'),
    
    # Auth endpoints
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/me/', UserProfileView.as_view(), name='user-profile'),
    path('auth/forgot-password/', ForgotPasswordView.as_view(), name='auth-forgot-password'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='auth-change-password'),

    # Authority and Government Official Workflow
    path('auth/authority-requests/', AuthorityRequestListView.as_view(), name='authority-requests-list'),
    path('auth/authority-requests/<int:pk>/action/', AuthorityApprovalView.as_view(), name='authority-request-action'),
    path('auth/official-reset-requests/', OfficialResetRequestsListView.as_view(), name='official-reset-requests-list'),
    path('auth/official-reset-requests/<int:pk>/action/', OfficialResetActionView.as_view(), name='official-reset-action'),
    path('auth/reroute-reports/', RerouteReportsView.as_view(), name='reroute-reports'),
]
