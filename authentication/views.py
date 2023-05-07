from authentication.resources.constants import (
    VERIFICATION_EMAIL_BODY, VERIFICATION_EMAIL_SUBJECT,
    VERIFICATION_SUCCESS, VERIFICATION_ACTIVATION_EXPIRED,
    VERIFICATION_INVALID_TOKEN, USER_REGISTRATION_SUCCESSFUL,
    INVALID_USER, APP_SCHEME, WRONG_AUTH_PROVIDER_MESSAGE, AUTH_PROVIDERS,
    HTTP, HTTPS, HOST_LOCAL, HOST_GLOBAL, HOST_GLOBAL_FRONTEND, RESET_PASSWORD_PATH, RESET_PASSWORD_MESSAGE,
    RESET_PASSWORD_EMAIL_SUBJECT, NO_USER_REGISTERED_WITH_EMAIL,
    RESET_PASSWORD_LINK_SENT_MESSAGE, USER_NOT_RECOGNISED, INVALID_TOKEN,
    VALID_TOKEN_PASSWORD_RESET, INVALID_RESET_PASSWORD_LINK,
    RESET_PASSWORD_SUCCESS, RESET_PASSWORD_FAIL_WRONG_AUTH_PROVIDER,
    INCORRECT_PASSWORD, CHANGE_PASSWORD_SUCCESS
)
from rest_framework import generics, status, views, permissions
from .serializers import (
    RegisterSerializer, SetNewPasswordSerializer,
    ResetPasswordEmailRequestSerializer, EmailVerificationSerializer,
    LoginSerializer, LogoutSerializer, PasswordChangeSerializer)

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
        response = dict(data={}, message="", error="")
        user_id = request._auth.payload.get('user_id', None)
        user_data = User.objects.get(id=user_id)
        logger.info(user_data)
        response['data'] = {'email': user_data.email}
        response['message'] = 'Successfully retrieved user email'
        return Response(response, status=status.HTTP_200_OK)


# Completed: Working as expected
class RegisterView(generics.GenericAPIView):
    serializer_class = RegisterSerializer
    renderer_classes = (UserRenderer,)

    def post(self, request):
        response = dict(data={}, message="", error="")
        request_data = request.data
        serializer = self.serializer_class(data=request_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        user_data = serializer.data

        user_obj = User.objects.get(email=user_data['email'])
        token = RefreshToken.for_user(
            user_obj).access_token  # Adds token to outstanding token list and provides access_token

        verify_absolute_url = HOST_GLOBAL_FRONTEND + "email/verify/?token=" + str(token)

        email_body = VERIFICATION_EMAIL_BODY + verify_absolute_url
        email_data = {'email_body': email_body, 'to_email': user_obj.email,
                      'email_subject': VERIFICATION_EMAIL_SUBJECT}
        Util.send_email(email_data)
        response['data'] = {'email': user_obj.email}
        response['message'] = USER_REGISTRATION_SUCCESSFUL,
        logger.info(response)
        return Response(response, status=status.HTTP_201_CREATED)


# Completed: Working as expected
class VerifyEmail(views.APIView):
    serializer_class = EmailVerificationSerializer

    def post(self, request):
        token = request.data.get('token')
        response = dict(data={}, message="", error="")

        try:
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
        response = dict(data={}, message="", error="")
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        response['data'] = serializer.data
        logger.info(response)
        result = Response(response, status=status.HTTP_200_OK)
        result.set_cookie('auth_token', serializer.data.get('access'))
        result.set_cookie('refresh_token', serializer.data.get('refresh'))
        return result


class LogoutAPIView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = LogoutSerializer

    def post(self, request):
        response = dict(data={}, message="", error="")
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            response['data'] = {'status': 205}
            logger.info(response)
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            logger.exception(e)
            return Response(status=status.HTTP_400_BAD_REQUEST)


class RequestPasswordResetEmail(generics.GenericAPIView):
    serializer_class = ResetPasswordEmailRequestSerializer

    def post(self, request):
        response = dict(data={}, message="", error="")
        serializer = self.serializer_class(data=request.data)

        email = request.data.get('email', '')

        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)

            # CHECK IF THE PROVIDER IS EMAIL, ELSE ERROR
            if user.auth_provider != AUTH_PROVIDERS['email']:
                response['error'] = WRONG_AUTH_PROVIDER_MESSAGE + user.auth_provider
                logger.info(response)
                return Response(response)

            uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)

            # relativeLink = reverse('password-reset-confirm', kwargs={'uidb64': uidb64, 'token': token})
            # redirect_url = request.data.get('redirect_url', '')
            absurl = HOST_LOCAL + RESET_PASSWORD_PATH + uidb64 + "/" + token

            email_body = RESET_PASSWORD_MESSAGE + absurl

            data = {'email_body': email_body, 'to_email': user.email,
                    'email_subject': RESET_PASSWORD_EMAIL_SUBJECT}

            Util.send_email(data)
        else:
            response['error'] = NO_USER_REGISTERED_WITH_EMAIL
            logger.info(response)
            return Response(response)
        response['message'] = RESET_PASSWORD_LINK_SENT_MESSAGE
        logger.info(response)
        return Response(response, status=status.HTTP_200_OK)


class PasswordTokenCheckAPI(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def get(self, request, uidb64, token):
        response = dict(data={}, message="", error="")
        try:
            id = smart_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=id)

            if not user:
                response['error'] = USER_NOT_RECOGNISED
                logger.info(response)
                return Response(response)

            if not PasswordResetTokenGenerator().check_token(user, token):
                response['error'] = INVALID_TOKEN
                logger.info(response)
                return Response(response)

            response['message'] = VALID_TOKEN_PASSWORD_RESET
            response['success'] = True
            logger.info(response)
            return Response(response)

        except DjangoUnicodeDecodeError as identifier:
            response['error'] = INVALID_RESET_PASSWORD_LINK
            logger.exception(identifier)
            return Response(response)


class SetNewPasswordAPIView(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def patch(self, request):
        response = dict(data={}, message="", error="")
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        response['message'] = RESET_PASSWORD_SUCCESS
        response['success'] = True
        logger.info(response)
        return Response(response, status=status.HTTP_200_OK)


# TO ALLOW LOGGED IN USER TO CHANGE HIS PASSWORD
class PasswordChangeAPIView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = PasswordChangeSerializer

    def patch(self, request):
        response = dict(data={}, message="", error="")
        user_id = request._auth.payload.get('user_id', None)
        email = self.request.user.email
        user_instance = User.objects.get(id=user_id)
        if user_instance.auth_provider != AUTH_PROVIDERS['email']:
            response['message'] = RESET_PASSWORD_FAIL_WRONG_AUTH_PROVIDER + user_instance.auth_provider
            response['success'] = False
            logger.info(response)
            return Response(response)

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.data['password']
        new_password = serializer.data['new_password']
        user = auth.authenticate(email=email, password=password)
        if not user:
            response['error'] = INCORRECT_PASSWORD
            logger.info(response)
            raise AuthenticationFailed(INCORRECT_PASSWORD)
        user.set_password(new_password)
        user.save()
        response['message'] = CHANGE_PASSWORD_SUCCESS
        response['success'] = True
        logger.info(response)
        return Response(response, status=status.HTTP_200_OK)
