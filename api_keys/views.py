from rest_framework import generics, status, request
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from authentication.models import User
from user_profile.models import UserProfile
from .models import APIKey
from .serializers import APIKeySerializer
from api_keys.apps import logger
from api_keys.resources.constants import (
    GET_API_KEYS_SUCCESS, USER_ID_AUTH_ID_MISMATCH, CREATE_APIKEY_SUCCESS,
    CREATE_APIKEY_FAIL, EXCEPTION_OCCURRED, DELETE_API_KEY_SUCCESS,
    DELETE_API_KEY_FAIL, API_KEY_INVALID, USER_PROFILE_SUCCESS_FOUND,
    USER_PROFILE_FAIL_NOT_FOUND
)


class APIKeyGetCreateUpdate(generics.GenericAPIView):
    serializer_class = APIKeySerializer
    permission_classes = [IsAuthenticated | IsAdminUser, ]

    def get(self, request):
        response = dict(data=dict(), message="", error="")

        try:
            user_id = self.request.user.id
            queryset = APIKey.objects.filter(user=user_id)
            serializer = self.serializer_class(queryset, many=True)
            data = serializer.data

            response['data'] = data
            response['message'] = GET_API_KEYS_SUCCESS
            logger.info(response)
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            response['message'] = EXCEPTION_OCCURRED
            response['error'] = str(e)
            logger.info(response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        response = dict(data=dict(), message="", error="")

        try:
            user_id = self.request.user.id
            # user_id_in_request = request.data['user']
            # if str(user_id) != str(user_id_in_request):
            #     return Response(USER_ID_AUTH_ID_MISMATCH,
            #                     status=status.HTTP_400_BAD_REQUEST)
            data = dict()
            data['user'] = user_id
            serializer = self.serializer_class(data=data)

            if serializer.is_valid():
                serializer.save()
                data = serializer.data
                response['data'] = data
                response['message'] = CREATE_APIKEY_SUCCESS
                logger.info(response)
                return Response(response, status=status.HTTP_200_OK)
            response['message'] = CREATE_APIKEY_FAIL
            response['error'] = serializer.errors
            logger.error(response['error'])
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            response['message'] = CREATE_APIKEY_FAIL
            response['error'] = str(e)
            logger.error(response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class APIKeyDelete(generics.GenericAPIView):
    serializer_class = APIKeySerializer
    permission_classes = [IsAuthenticated | IsAdminUser, ]

    def delete(self, request, api_key=None):
        response = dict(data=dict(), message="", error="")

        try:
            user_id = self.request.user.id
            api_key_obj = APIKey.objects.get(id=api_key)
            if str(api_key_obj.user.id) != str(user_id):
                return Response(USER_ID_AUTH_ID_MISMATCH,
                                status=status.HTTP_400_BAD_REQUEST)
            api_key_obj.delete()
            response['data'] = {'api_key': api_key}
            response['message'] = DELETE_API_KEY_SUCCESS
            logger.info(response)
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response['data'] = {'api_key': api_key}
            response['message'] = EXCEPTION_OCCURRED
            response['error'] = str(e)
            logger.info(response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class APIKeyGetSCW(generics.GenericAPIView):
    serializer_class = APIKeySerializer
    permission_classes = [AllowAny, ]

    def get(self, request, api_key):
        response = dict(data=dict(), message="", error="")

        try:
            api_key_obj = APIKey.objects.get(id=api_key)
            if not api_key_obj:
                response['message'] = API_KEY_INVALID
                logger.info(response)
                return Response(response, status=status.HTTP_200_OK)
            user_profile_obj = User.objects.get(user=api_key_obj.user)
            if not user_profile_obj:
                response['message'] = USER_PROFILE_FAIL_NOT_FOUND
                return Response(response, status=status.HTTP_200_OK)
            smart_contract_wallet_address = user_profile_obj.user_smart_contract_wallet_address
            response['data'] = {'smart_contract_wallet_address': smart_contract_wallet_address}
            response['message'] = USER_PROFILE_SUCCESS_FOUND
            logger.info(response)
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response['message'] = EXCEPTION_OCCURRED
            response['error'] = str(e)
            logger.info(response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
























class APIKeyDelete(generics.GenericAPIView):
    serializer_class = APIKeySerializer
    permission_classes = [IsAuthenticated | IsAdminUser, ]

    def delete(self, request, api_key=None):
        response = dict(data={}, message="", error="")
        try:
            user_id = self.request.user.id
            api_key_obj = APIKey.objects.get(id=api_key)
            if str(api_key_obj.user.id) != str(user_id):
                return Response(USER_ID_AUTH_ID_MISMATCH,
                                status=status.HTTP_400_BAD_REQUEST)

            api_key_obj.delete()

            response['data'] = {'api_key': api_key}
            response['message'] = DELETE_API_KEY_SUCCESS
            logger.info(response)
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response['data'] = {'api_key': api_key}
            response['message'] = EXCEPTION_OCCURRED
            response['error'] = str(e)
            logger.info(response)
            return Response(response, status=status.HTTP_200_OK)


class APIKeyGetSCW(generics.GenericAPIView):
    serializer_class = APIKeySerializer
    permission_classes = [AllowAny, ]

    def get(self, request, api_key):
        response = dict(data={}, message="", error="")
        try:
            api_key_obj = APIKey.objects.get(id=api_key)
            if not api_key_obj:
                response['message'] = 'API Key Invalid'
                logger.info(response)
                return Response(response, status=status.HTTP_200_OK)
            user_profile_obj = UserProfile.objects.get(user=api_key_obj.user)
            if not user_profile_obj:
                response['message'] = 'User Profile not found'
                return Response(response, status=status.HTTP_200_OK)

            smart_contract_wallet_address = user_profile_obj.user_smart_contract_wallet_address
            response['data'] = {'smart_contract_wallet_address': smart_contract_wallet_address}
            response['message'] = 'Success!'
            logger.info(response)
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            response['message'] = EXCEPTION_OCCURRED
            response['error'] = str(e)
            logger.info(response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
