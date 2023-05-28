from rest_framework import generics, status, request
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from authentication.models import User
from api_keys.models import APIKey
from .models import KYCProfile, KYCProvider, KYCProfilePolygonId, KYCProfileRequiredSchema
from .serializers import KYCProfileSerializer, KYCProviderSerializer, \
    KYCProfileClaimRequestSerializer, KYCProfilePolygonIdSerializer, KYCProfileRequiredSchemaSerializer
from .constants import (
    CREATE_KYC_PROFILE_SUCCESS, CREATE_KYC_PROFILE_FAIL, GET_KYC_PROFILE_SUCCESS,
    GET_KYC_PROFILE_FAIL, UPDATE_KYC_PROFILE_SUCCESS, UPDATE_KYC_PROFILE_FAIL,
    DELETE_KYC_PROFILE_SUCCESS, DELETE_KYC_PROFILE_FAIL, CREATE_POLYGON_ID_SUCCESS,
    CREATE_POLYGON_ID_FAIL, API_KEY_INVALID, API_KEY_NOT_FOUND,
    CREATE_KYC_PROFILE_REQUIRED_SCHEMA_SUCCESS, CREATE_KYC_PROFILE_REQUIRED_SCHEMA_FAIL)


class KYCProviderListCreate(generics.ListCreateAPIView):
    serializer_class = KYCProviderSerializer
    queryset = KYCProvider.objects.all()
    permission_classes = [IsAdminUser]


class KYCProviderRetrieveUpdateDelete(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = KYCProviderSerializer
    queryset = KYCProvider.objects.all()
    permission_classes = [IsAdminUser]
    lookup_field = "id"


class KYCProfileGetCreateUpdateDelete(generics.GenericAPIView):
    serializer_class = KYCProfileSerializer
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        response = dict(data=dict(), message="", error="")

        try:
            user_id = self.request.user.id
            queryset = KYCProfile.objects.get(user=user_id)
            serializer = self.serializer_class(queryset)
            data = serializer.data
            response['data'] = data
            response['message'] = GET_KYC_PROFILE_SUCCESS
            # logger.info(response)
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response['message'] = GET_KYC_PROFILE_FAIL
            response['error'] = str(e)
            # logger.info(response)
            return Response(response, status=status.HTTP_200_OK)

    def post(self, request):
        response = dict(data=dict(), message="", error="")

        try:
            user_id = self.request.user.id
            request.data['user'] = user_id

            # KYC Provider - synaps as default
            kyc_provider_obj = KYCProvider.objects.get(name='Synaps')
            request.data['kyc_provider'] = kyc_provider_obj.id

            # kyc_verification_provider
            request.data['kyc_verification_status'] = 'Pending'

            serializer = self.serializer_class(data=request.data)

            if serializer.is_valid():
                serializer.save()
                data = serializer.data
                response['data'] = data
                response['message'] = CREATE_KYC_PROFILE_SUCCESS

                # logger.info(response)
                return Response(response, status=status.HTTP_200_OK)
            response['message'] = CREATE_KYC_PROFILE_FAIL
            response['error'] = serializer.errors
            # logger.error(response['error'])
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            response['message'] = CREATE_KYC_PROFILE_FAIL
            response['error'] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        response = dict(data=dict(), message="", error="")

        try:
            user_id = self.request.user.id
            profile_obj = KYCProfile.objects.get(user=user_id)
            serializer = self.serializer_class(profile_obj, data=request.data)

            if serializer.is_valid():
                serializer.save()
                data = serializer.data
                response['data'] = data
                # logger.info(response)
                response['message'] = UPDATE_KYC_PROFILE_SUCCESS
                return Response(response, status=status.HTTP_200_OK)
            response['message'] = UPDATE_KYC_PROFILE_FAIL
            response['error'] = serializer.errors
            # logger.error(response['error'])
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            response['message'] = UPDATE_KYC_PROFILE_FAIL
            response['error'] = str(e)
            # logger.error(response['error'])
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        response = dict(data=dict(), message="", error="")

        try:
            user_id = self.request.user.id
            profile_obj = KYCProfile.objects.get(user=user_id)
            profile_obj.delete()
            response['message'] = DELETE_KYC_PROFILE_SUCCESS
            # logger.info(response)
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response['message'] = DELETE_KYC_PROFILE_FAIL
            response['error'] = str(e)
            # logger.info(response)
            return Response(response, status=status.HTTP_200_OK)


class KYCProviderClaimRequestListUpdate(generics.GenericAPIView):
    serializer_class = KYCProfileClaimRequestSerializer
    permission_classes = [AllowAny]

    def get(self, request):
        response = dict(data=dict(), message="", error="")

        try:
            kyc_provider = request.query_params.get('kyc_provider')
            kyc_provider_obj = KYCProvider.objects.get(name=kyc_provider)
            kyc_provider_id = kyc_provider_obj.id

            queryset = KYCProfile.objects.filter(kyc_provider=kyc_provider_id)
            serializer = self.serializer_class(queryset, many=True)

            data = serializer.data
            response['data'] = data
            response['message'] = GET_KYC_PROFILE_SUCCESS
            # logger.info(response)
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response['message'] = GET_KYC_PROFILE_FAIL
            response['error'] = str(e)
            # logger.info(response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        response = dict(data={}, message="", error="")

        # KYC Provider - synaps as default
        try:
            kyc_profile_obj = KYCProfile.objects.get(id=request.data.get('id'))
            kyc_verification_status = request.data.get('kyc_verification_status')
            kyc_profile_obj.kyc_verification_status = kyc_verification_status
            kyc_profile_obj.save()
            request.data['kyc_verification_status'] = kyc_profile_obj.kyc_verification_status
            response['data'] = request.data
            response['message'] = CREATE_KYC_PROFILE_SUCCESS
            # logger.info(response)
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response['message'] = CREATE_KYC_PROFILE_FAIL
            response['error'] = str(e)
            # logger.error(response['error'])
            return Response(response, status=status.HTTP_200_OK)

    # def put(self, request):
    #     response = dict(data=dict(), message="", error="")
    #     kyc_profile_id = self.request.data.get('id')
    #     print('kyc_profile_id:', kyc_profile_id)
    #     profile_obj = KYCProfile.objects.get(id=kyc_profile_id)
    #
    #     serializer = self.serializer_class(profile_obj, data=request.data)
    #
    #     if serializer.is_valid():
    #         serializer.save()
    #         data = serializer.data
    #         response['data'] = data
    #         # logger.info(response)
    #         response['message'] = UPDATE_KYC_PROFILE_SUCCESS
    #         return Response(response, status=status.HTTP_200_OK)
    #     response['message'] = UPDATE_KYC_PROFILE_FAIL
    #     response['error'] = serializer.errors
    #     # logger.error(response['error'])
    #     return Response(response, status=status.HTTP_400_BAD_REQUEST)


class KYCProfilePolygonIdGetCreateUpdateDelete(generics.GenericAPIView):
    serializer_class = KYCProfilePolygonIdSerializer
    permission_classes = [AllowAny, ]

    def get(self, request):
        response = dict(data=dict(), message="", error="")

        try:
            kyc_profile_id = self.request.query_params.get('id')
            queryset = KYCProfilePolygonId.objects.filter(kyc_profile=kyc_profile_id)
            # if len(queryset) > 0:
            #     queryset = queryset[0]
            serializer = self.serializer_class(queryset, many=True)
            data = serializer.data
            response['data'] = data
            response['message'] = GET_KYC_PROFILE_SUCCESS
            # logger.info(response)
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response['message'] = GET_KYC_PROFILE_FAIL
            response['error'] = str(e)
            # logger.info(response)
            return Response(response, status=status.HTTP_200_OK)

    def post(self, request):
        response = dict(data=dict(), message="", error="")

        try:
            serializer = self.serializer_class(data=request.data)

            if serializer.is_valid():
                serializer.save()
                data = serializer.data
                response['data'] = data
                response['message'] = CREATE_POLYGON_ID_SUCCESS

                # logger.info(response)
                return Response(response, status=status.HTTP_200_OK)
            response['message'] = CREATE_POLYGON_ID_FAIL
            response['error'] = serializer.errors
            # logger.error(response['error'])
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            response['message'] = CREATE_POLYGON_ID_FAIL
            response['error'] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        response = dict(data=dict(), message="", error="")

        try:
            kyc_profile_id = self.request.data.get('id')
            polygon_id_obj = KYCProfilePolygonId.objects.get(kyc_profile=kyc_profile_id)
            serializer = self.serializer_class(polygon_id_obj, data=request.data)

            if serializer.is_valid():
                serializer.save()
                data = serializer.data
                response['data'] = data
                # logger.info(response)
                response['message'] = UPDATE_KYC_PROFILE_SUCCESS
                return Response(response, status=status.HTTP_200_OK)
            response['message'] = UPDATE_KYC_PROFILE_FAIL
            response['error'] = serializer.errors
            # logger.error(response['error'])
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            response['message'] = UPDATE_KYC_PROFILE_FAIL
            response['error'] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    # def delete(self, request):
    #     response = dict(data=dict(), message="", error="")
    #
    #     try:
    #         user_id = self.request.user.id
    #         profile_obj = KYCProfile.objects.get(user=user_id)
    #         profile_obj.delete()
    #         response['message'] = DELETE_KYC_PROFILE_SUCCESS
    #         # logger.info(response)
    #         return Response(response, status=status.HTTP_200_OK)
    #
    #     except Exception as e:
    #         response['message'] = DELETE_KYC_PROFILE_FAIL
    #         response['error'] = str(e)
    #         return Response(response, status=status.HTTP_400_BAD_REQUEST)


class KYCProfileRequiredSchemaView(generics.GenericAPIView):
    serializer_class = KYCProfileRequiredSchemaSerializer
    permission_classes = [AllowAny, ]

    def get(self, request):
        response = dict(data=dict(), message="", error="")

        # Validate api_key and user_id
        try:
            api_key = request.query_params.get('api_key', None)
            api_key_in_db = APIKey.objects.filter(id=api_key)
            if len(api_key_in_db) == 0:
                response['message'] = API_KEY_NOT_FOUND
                return Response(response, status=status.HTTP_200_OK)

            user_id_for_api_key_in_db = api_key_in_db[0].user.id

            queryset = KYCProfileRequiredSchema.objects.filter(user=user_id_for_api_key_in_db)
            serializer = self.serializer_class(queryset, many=True)
            data = serializer.data
            response['data'] = data
            response['message'] = GET_KYC_PROFILE_SUCCESS
            # logger.info(response)
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response['message'] = GET_KYC_PROFILE_FAIL
            response['error'] = str(e)
            # logger.info(response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        response = dict(data=dict(), message="", error="")

        try:
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                serializer.save()
                data = serializer.data
                response['data'] = data
                response['message'] = CREATE_KYC_PROFILE_REQUIRED_SCHEMA_SUCCESS
                # logger.info(response)
                return Response(response, status=status.HTTP_200_OK)
            response['message'] = CREATE_KYC_PROFILE_REQUIRED_SCHEMA_FAIL
            response['error'] = serializer.errors
            # logger.error(response['error'])
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response['message'] = CREATE_KYC_PROFILE_REQUIRED_SCHEMA_FAIL
            response['error'] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
