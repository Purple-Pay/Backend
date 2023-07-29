from rest_framework import serializers
from authentication.resources.constants import (
    AUTH_FAIL_USER_INACTIVE, AUTH_FAIL_INVALID_CREDENTIALS,
    AUTH_FAIL_USER_CREATOR_VERIFICATION_PENDING, AUTH_FAIL_EMAIL_NOT_VERIFIED,
    INVALID_PHONE_NUMBER,
    AUTH_PROVIDERS, BAD_TOKEN)

from .models import User
from django.contrib import auth
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import phonenumbers
import json


class RegisterSerializer(serializers.ModelSerializer):
    default_error_messages = {
        'phone_number': INVALID_PHONE_NUMBER,
    }

    class Meta:
        model = User
        fields = ['email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    # def validate(self, data):
    #     """
    #     Check phone number
    #     """
    #     phone_number = data.get('phone_number', '')  # validation at frontend also
    #     if phone_number:
    #         try:
    #             parsed_number = phonenumbers.parse(phone_number)
    #             # Errors in cases where parsing is success but number is invalid
    #             if not phonenumbers.is_valid_number(parsed_number):
    #                 raise serializers.ValidationError(self.default_error_messages)
    #
    #             # Exception in case parsing breaks
    #         except phonenumbers.NumberParseException:
    #             raise serializers.ValidationError(self.default_error_messages)
    #
    #     return data

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class EmailVerificationResendSerializer(serializers.Serializer):
    email = serializers.EmailField(min_length=2)
    redirect_url = serializers.CharField(max_length=500, required=False)

    class Meta:
        fields = ['email']

class EmailVerificationSerializer(serializers.ModelSerializer):
    token = serializers.CharField(max_length=555)

    class Meta:
        model = User
        fields = ['token']


class LoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255, min_length=3, write_only=True)
    password = serializers.CharField(max_length=68, min_length=3, write_only=True)
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'access', 'refresh']

    def validate(self, attrs):
        email = attrs.get('email', '')
        password = attrs.get('password', '')
        filtered_user_by_email = User.objects.filter(email=email)
        user = auth.authenticate(email=email, password=password)

        if filtered_user_by_email.exists() and filtered_user_by_email[0].auth_provider != AUTH_PROVIDERS.get('email'):
            raise AuthenticationFailed(detail='Please continue your login using '
                                              + filtered_user_by_email[0].auth_provider)
        if not user:
            raise AuthenticationFailed(AUTH_FAIL_INVALID_CREDENTIALS)
        if not user.is_active:
            raise AuthenticationFailed(AUTH_FAIL_USER_INACTIVE)
        if not user.is_verified:
            raise AuthenticationFailed(AUTH_FAIL_EMAIL_NOT_VERIFIED)

        refresh = TokenObtainPairSerializer.get_token(user)  # CustomTokenObtainPairSerializer
        payload = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        return payload


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    default_error_messages = {
        'bad_token': BAD_TOKEN
    }

    def validate(self, attrs):
        self.token = attrs['refresh']
        return attrs

    def save(self, **kwargs):
        try:
            RefreshToken(self.token).blacklist()
        except TokenError:
            self.fail('bad_token')


class ResetPasswordEmailRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(min_length=2)
    redirect_url = serializers.CharField(max_length=500, required=False)

    class Meta:
        fields = ['email']


class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(
        min_length=3, max_length=68, write_only=True)
    token = serializers.CharField(
        min_length=1, write_only=True)
    uidb64 = serializers.CharField(
        min_length=1, write_only=True)

    class Meta:
        fields = ['password', 'token', 'uidb64']

    def validate(self, attrs):
        try:
            password = attrs.get('password')
            token = attrs.get('token')
            uidb64 = attrs.get('uidb64')

            id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=id)

            if not user:
                raise AuthenticationFailed('User not found, the reset link is invalid', 401)

            if not PasswordResetTokenGenerator().check_token(user, token):
                raise AuthenticationFailed('The reset link is invalid', 401)

            user.set_password(password)
            user.save()
            return (user)

        except Exception as e:
            raise AuthenticationFailed('The reset link is invalid', 401)
        # return super().validate(attrs)


class PasswordChangeSerializer(serializers.Serializer):
    password = serializers.CharField(
        max_length=68, min_length=3)
    new_password = serializers.CharField(
        max_length=68, min_length=3)

    class Meta:
        fields = ['password', 'new_password']
