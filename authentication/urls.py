from django.urls import path
from .views import (
    RegisterView, LogoutAPIView, SetNewPasswordAPIView,
    VerifyEmail, LoginAPIView, PasswordTokenCheckAPI,
    RequestPasswordResetEmail, PasswordChangeAPIView, UserDetails,
    VerfiyEmailResend)
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name="register"),
    path('verify_email_resend/', VerfiyEmailResend.as_view(), name="verify_email_resend"),
    path('token/', LoginAPIView.as_view(), name="login"),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutAPIView.as_view(), name="logout"),

    path('email_verify/', VerifyEmail.as_view(), name="email_verify"),

    path('request_reset_email/', RequestPasswordResetEmail.as_view(),
         name="request_reset_email"),
    path('password-reset/<uidb64>/<token>/',
         PasswordTokenCheckAPI.as_view(), name='password_reset_confirm'),
    path('password_reset_complete', SetNewPasswordAPIView.as_view(),
         name='password_reset_complete'),
    path('change_password/', PasswordChangeAPIView.as_view(), name='change_password'),
    # path('profile_detail/', UserDetails.as_view(), name='user_details')
]
