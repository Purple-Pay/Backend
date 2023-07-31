from authentication.resources.constants import (
    VERIFICATION_EMAIL_BODY, VERIFICATION_EMAIL_SUBJECT,
    VERIFICATION_SUCCESS, VERIFICATION_ACTIVATION_EXPIRED,
    VERIFICATION_INVALID_TOKEN, USER_REGISTRATION_SUCCESS, USER_REGISTRATION_FAIL,
    AUTH_SUCCESS, AUTH_FAIL_INVALID_CREDENTIALS, AUTH_FAIL,
    AUTH_FAIL_USER_INACTIVE, AUTH_FAIL_EMAIL_NOT_VERIFIED,
    AUTH_FAIL_USER_CREATOR_VERIFICATION_PENDING, LOGOUT_SUCCESS, LOGOUT_FAIL, RESET_PASSWORD_FAIL,
    INVALID_USER, APP_SCHEME, WRONG_AUTH_PROVIDER_MESSAGE, AUTH_PROVIDERS,
    HTTP, HTTPS, HOST_LOCAL,
    HOST_GLOBAL_BACKEND_DEV, HOST_GLOBAL_FRONTEND_DEV,
    HOST_GLOBAL_BACKEND_STAGING, HOST_GLOBAL_FRONTEND_STAGING,
    HOST_GLOBAL_BACKEND_PROD, HOST_GLOBAL_FRONTEND_PROD,
    RESET_PASSWORD_PATH, RESET_PASSWORD_MESSAGE,
    RESET_PASSWORD_EMAIL_SUBJECT, NO_USER_REGISTERED_WITH_EMAIL,
    RESET_PASSWORD_LINK_SENT_MESSAGE, USER_NOT_RECOGNISED, INVALID_TOKEN,
    VALID_TOKEN_PASSWORD_RESET, INVALID_RESET_PASSWORD_LINK,
    RESET_PASSWORD_SUCCESS, RESET_PASSWORD_FAIL_WRONG_AUTH_PROVIDER,
    INCORRECT_PASSWORD, CHANGE_PASSWORD_SUCCESS, CHANGE_PASSWORD_FAIL, FETCH_USER_DETAILS_SUCCESS,
    FETCH_USER_DETAILS_FAIL, EMAIL_SEND_SUCCESSFULLY, UNABLE_TO_RESEND_EMAIL
)
from rest_framework import generics, status, views, permissions
from .serializers import (
    RegisterSerializer, SetNewPasswordSerializer,
    ResetPasswordEmailRequestSerializer, EmailVerificationSerializer,
    LoginSerializer, LogoutSerializer, PasswordChangeSerializer, EmailVerificationResendSerializer)

from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
import jwt
from django.conf import settings
from .renderers import UserRenderer
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, smart_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from .utils import Util
from django.http import HttpResponsePermanentRedirect
from rest_framework.exceptions import AuthenticationFailed
import os
from django.contrib import auth
from authentication.apps import logger
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template.loader import render_to_string


class CustomRedirect(HttpResponsePermanentRedirect):
    allowed_schemes = [APP_SCHEME, HTTP, HTTPS]


class UserDetails(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, ]

    def get(self, request):
        response = dict(data=dict(), message="", error="")

        try:
            user_id = request._auth.payload.get('user_id', None)
            user_data = User.objects.get(id=user_id)
            logger.info(user_data)
            response['data'] = {'email': user_data.email}
            response['message'] = FETCH_USER_DETAILS_SUCCESS
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response['message'] = FETCH_USER_DETAILS_FAIL
            response['error'] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

def get_redirect_url():
    deployed_env = os.environ.get('BUILD_ENV', 'dev')
    print('test',deployed_env)
    if deployed_env == 'sit':
        return HOST_GLOBAL_FRONTEND_STAGING
    if deployed_env == 'prod':
        return HOST_GLOBAL_FRONTEND_PROD
    return HOST_GLOBAL_FRONTEND_DEV

# Completed: Working as expected
class RegisterView(generics.GenericAPIView):
    serializer_class = RegisterSerializer
    renderer_classes = (UserRenderer,)

    def post(self, request):
        response = dict(data=dict(), message="", error="")
        try:
            request_data = request.data
            serializer = self.serializer_class(data=request_data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            user_data = serializer.data

            user_obj = User.objects.get(email=user_data['email'])
            token = RefreshToken.for_user(
                user_obj).access_token  # Adds token to outstanding token list and provides access_token

            redirect_url = get_redirect_url()
            verify_absolute_url = redirect_url + "email/verify/?token=" + str(token)

            # email_body = VERIFICATION_EMAIL_BODY + verify_absolute_url
            email_body = render_to_string('email_verify.html', {'url': verify_absolute_url})
            email_data = {'email_body': email_body, 'to_email': [user_obj.email],
                          'email_subject': VERIFICATION_EMAIL_SUBJECT}
            Util.send_email(email_data, html=True, img=('images/image-1.png', '<logo>'))

            response['data'] = {'email': user_obj.email}
            response['message'] = USER_REGISTRATION_SUCCESS
            logger.info(response)
            return Response(response, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.info(str(e))
            response['message'] = USER_REGISTRATION_FAIL
            response['error'] = str(e)
            logger.info(response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

class VerfiyEmailResend(generics.GenericAPIView):
    serializer_class = EmailVerificationResendSerializer
    renderer_classes = (UserRenderer,)

    def post(self, request):
        response = dict(data=dict(), message="", error="")
        try:
            email = request.data.get('email', '')
            if User.objects.filter(email=email).exists():
                user_obj = User.objects.get(email=email)
                token = RefreshToken.for_user(
                    user_obj).access_token  # Adds token to outstanding token list and provides access_token

                redirect_url = get_redirect_url()
                verify_absolute_url = redirect_url + "email/verify/?token=" + str(token)

                # email_body = VERIFICATION_EMAIL_BODY + verify_absolute_url
                email_body = render_to_string('email_verify.html', {'url': verify_absolute_url})
                email_data = {'email_body': email_body, 'to_email': [user_obj.email],
                              'email_subject': VERIFICATION_EMAIL_SUBJECT}
                Util.send_email(email_data, html=True, img=('images/image-1.png', '<logo>'))
            else:
                response['message'] = NO_USER_REGISTERED_WITH_EMAIL
                logger.info(response)
                return Response(response, status=status.HTTP_200_OK)
            response['data'] = {'email': user_obj.email}
            response['message'] = EMAIL_SEND_SUCCESSFULLY
            logger.info(response)
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            logger.info(str(e))
            response['message'] = UNABLE_TO_RESEND_EMAIL
            response['error'] = str(e)
            logger.info(response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

# Completed: Working as expected
class VerifyEmail(views.APIView):
    serializer_class = EmailVerificationSerializer

    def post(self, request):
        response = dict(data=dict(), message="", error="")

        try:
            token = request.data.get('token')
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user = User.objects.get(id=payload['user_id'])
            if not user:
                response['message'] = INVALID_USER
                logger.info(response)
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            if not user.is_verified:
                user.is_verified = True
                user.save()
            response['message'] = VERIFICATION_SUCCESS
            logger.info(response)
            return Response(response, status=status.HTTP_200_OK)

        except jwt.ExpiredSignatureError as identifier:
            logger.error(identifier)
            response['message'] = VERIFICATION_ACTIVATION_EXPIRED
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        except jwt.exceptions.DecodeError as identifier:
            logger.exception(identifier)
            response['message'] = VERIFICATION_INVALID_TOKEN
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


# Completed: Working as expected
class LoginAPIView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request):
        response = dict(data=dict(), message="", error="")

        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            response['data'] = serializer.data
            response['message'] = AUTH_SUCCESS
            logger.info(response)
            result = Response(response, status=status.HTTP_200_OK)
            result.set_cookie('auth_token', serializer.data.get('access'))
            result.set_cookie('refresh_token', serializer.data.get('refresh'))
            return result

        except Exception as e:
            response['message'] = AUTH_FAIL
            response['error'] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = LogoutSerializer

    def post(self, request):
        response = dict(data=dict(), message="", error="")
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            response['data'] = {'status': 205}
            response['message'] = LOGOUT_SUCCESS
            logger.info(response)
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            logger.exception(e)
            response['message'] = LOGOUT_FAIL
            response['error'] = str(e)
            return Response(status=status.HTTP_400_BAD_REQUEST)


class RequestPasswordResetEmail(generics.GenericAPIView):
    serializer_class = ResetPasswordEmailRequestSerializer

    def post(self, request):
        response = dict(data=dict(), message="", error="")

        try:
            serializer = self.serializer_class(data=request.data)
            email = request.data.get('email', '')
            if User.objects.filter(email=email).exists():
                user = User.objects.get(email=email)

                # Check if the provider is email, else throw error
                if user.auth_provider != AUTH_PROVIDERS['email']:
                    response['error'] = WRONG_AUTH_PROVIDER_MESSAGE + user.auth_provider
                    logger.info(response)
                    return Response(response)

                uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
                token = PasswordResetTokenGenerator().make_token(user)

                # relativeLink = reverse('password-reset-confirm', kwargs={'uidb64': uidb64, 'token': token})
                # redirect_url = request.data.get('redirect_url', '')
                redirect_url = get_redirect_url()
                reset_absolute_url = redirect_url + RESET_PASSWORD_PATH + uidb64 + "/" + token
                # email_body = RESET_PASSWORD_MESSAGE + reset_absolute_url
                email_body = render_to_string('email_reset_password.html', {'url': reset_absolute_url})
                email_data = {'email_body': email_body, 'to_email': [user.email],
                              'email_subject': RESET_PASSWORD_EMAIL_SUBJECT}
                Util.send_email(email_data, html=True, img=('images/image-1.png', '<logo>'))
            else:
                response['message'] = NO_USER_REGISTERED_WITH_EMAIL
                logger.info(response)
                return Response(response, status=status.HTTP_200_OK)
            response['message'] = RESET_PASSWORD_LINK_SENT_MESSAGE
            logger.info(response)
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            response['message'] = RESET_PASSWORD_FAIL
            response['error'] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class PasswordTokenCheckAPI(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def get(self, request, uidb64, token):
        response = dict(data=dict(), message="", error="")
        try:
            user_id = smart_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=user_id)

            if not user:
                response['message'] = USER_NOT_RECOGNISED
                logger.info(response)
                return Response(response, status=status.HTTP_200_OK)

            if not PasswordResetTokenGenerator().check_token(user, token):
                response['message'] = INVALID_TOKEN
                logger.info(response)
                return Response(response, status=status.HTTP_200_OK)

            response['data'] = {'success': True}
            response['message'] = VALID_TOKEN_PASSWORD_RESET
            logger.info(response)
            return Response(response, status.HTTP_200_OK)

        except DjangoUnicodeDecodeError as identifier:
            response['message'] = INVALID_RESET_PASSWORD_LINK
            response['error'] = str(identifier)
            logger.exception(identifier)
            return Response(response, status.HTTP_400_BAD_REQUEST)


class SetNewPasswordAPIView(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def patch(self, request):
        response = dict(data=dict(), message="", error="")

        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            response['data'] = {'success': True}
            response['message'] = RESET_PASSWORD_SUCCESS
            logger.info(response)
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response['message'] = RESET_PASSWORD_FAIL
            response['error'] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


# Allow Logged In User to change their password
class PasswordChangeAPIView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = PasswordChangeSerializer

    def patch(self, request):
        response = dict(data=dict(), message="", error="")

        try:
            user_id = request._auth.payload.get('user_id', None)
            email = self.request.user.email
            user_instance = User.objects.get(id=user_id)
            if user_instance.auth_provider != AUTH_PROVIDERS['email']:
                response['data'] = {'success': False}
                response['message'] = RESET_PASSWORD_FAIL_WRONG_AUTH_PROVIDER + user_instance.auth_provider
                logger.info(response)
                return Response(response, status=status.HTTP_200_OK)

            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            password = serializer.data['password']
            new_password = serializer.data['new_password']
            user = auth.authenticate(email=email, password=password)
            if not user:
                response['message'] = INCORRECT_PASSWORD
                logger.info(response)
                raise AuthenticationFailed(INCORRECT_PASSWORD)
            user.set_password(new_password)
            user.save()
            response['data'] = {'success': True}
            response['message'] = CHANGE_PASSWORD_SUCCESS
            logger.info(response)
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response['message'] = CHANGE_PASSWORD_FAIL
            response['error'] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
