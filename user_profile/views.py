from rest_framework import generics, status, request
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from authentication.models import User
from .models import UserProfile, UserType, UserSmartContractWalletAddress
from payments.models import BlockchainNetwork, Currency
from .serializers import UserProfileSerializer, UserTypeSerializer, UserSmartContractWalletAddressSerializer
import uuid
import datetime
from django.utils import timezone
import base64
from user_profile.apps import logger
from user_profile.resources.constants import (
    PROFILE_DOES_NOT_EXIST, GET_PROFILE_SUCCESS, CREATE_PROFILE_FAIL,
    UPDATE_PROFILE_FAIL, DELETE_PROFILE_SUCCESS, DELETE_PROFILE_FAIL,
    CREATE_USER_SMART_CONTRACT_WALLET_SUCCESS, CREATE_USER_SMART_CONTRACT_WALLET_FAIL
)


class UserProfileGetCreateUpdateDelete(generics.GenericAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        response = dict(data=dict(), message="", error="")

        try:
            user_id = self.request.user.id
            queryset = UserProfile.objects.get(user=user_id)
            user_obj = User.objects.get(id=user_id)
            serializer = self.serializer_class(queryset)
            data = serializer.data
            response['data'] = data
            # response['data']['phone_number'] = str(user_obj.phone_number)
            response['data']['email'] = user_obj.email
            response['message'] = GET_PROFILE_SUCCESS
            logger.info(response)
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response['message'] = PROFILE_DOES_NOT_EXIST
            response['error'] = str(e)
            logger.info(response)
            return Response(response, status=status.HTTP_200_OK)

    def post(self, request):
        response = dict(data=dict(), message="", error="")
        try:
            user_id = self.request.user.id
            request.data['user'] = user_id
            print(request.data)

            # user_obj = User.objects.get(id=user_id)
            # user_obj = User.objects.get(id=user_id)
            if request.data['first_name'] is None:
                response["message"] = "First Name is missing"
                return response
            if request.data['last_name'] is None:
                response["message"] = "Last Name is missing"
                return response
            if request.data['location'] is None:
                response["message"] = "Location is missing"
                return response
            if request.data['company'] is None:
                response["message"] = "Company is missing"
                return response

            serializer = self.serializer_class(data=request.data)

            if serializer.is_valid():
                # if 'phone_number' in request.data:
                #     user_obj.phone_number = request.data['phone_number']
                #     user_obj.save()
                serializer.save()

                data = serializer.data
                response['data'] = data
                # response['data']['phone_number'] = str(user_obj.phone_number)
                response['message'] = GET_PROFILE_SUCCESS

                logger.info(response)
                return Response(response, status=status.HTTP_200_OK)
            response['message'] = CREATE_PROFILE_FAIL
            response['error'] = serializer.errors
            logger.error(response['error'])
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            response['message'] = CREATE_PROFILE_FAIL
            response['error'] = str(e)
            logger.error(response['error'])
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        response = dict(data=dict(), message="", error="")

        try:
            user_id = self.request.user.id
            # user_obj = User.objects.get(id=user_id)
            profile_obj = UserProfile.objects.get(user=user_id)
            serializer = self.serializer_class(profile_obj, data=request.data)

            if serializer.is_valid():
                # if 'phone_number' in request.data:
                #     user_obj.phone_number = request.data['phone_number']
                #     user_obj.save()
                serializer.save()
                data = serializer.data
                response['data'] = data
                # response['data']['phone_number'] = str(user_obj.phone_number)
                logger.info(response)
                return Response(response, status=status.HTTP_200_OK)
            response['message'] = UPDATE_PROFILE_FAIL
            response['error'] = serializer.errors
            logger.error(response['error'])
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            response['message'] = UPDATE_PROFILE_FAIL
            response['error'] = str(e)
            logger.error(response['error'])
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        response = dict(data=dict(), message="", error="")

        try:
            user_id = self.request.user.id
            profile_obj = UserProfile.objects.get(user=user_id)
            profile_obj.delete()
            response['message'] = DELETE_PROFILE_SUCCESS
            logger.info(response)
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response['message'] = DELETE_PROFILE_FAIL
            response['error'] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class UserTypeListCreate(generics.ListCreateAPIView):
    serializer_class = UserTypeSerializer
    queryset = UserType.objects.all()
    permission_classes = [IsAdminUser]


class UserTypeRetrieveUpdateDelete(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserTypeSerializer
    queryset = UserType.objects.all()
    permission_classes = [IsAdminUser]
    lookup_field = "id"


class UserSmartContractWalletAddressGetCreateUpdateDelete(generics.GenericAPIView):
    serializer_class = UserSmartContractWalletAddressSerializer
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        response = dict(data=dict(), message="", error="")

        try:
            user_id = self.request.user.id
            queryset = UserSmartContractWalletAddress.objects.filter(user=user_id)
            serializer = self.serializer_class(queryset, many=True)
            data = serializer.data
            response['data']['user'] = user_id
            for idx in range(len(data)):
                data[idx].pop('id')
                data[idx].pop('created_at')
                data[idx].pop('modified_at')
                data[idx].pop('user')
                data[idx]['chain_id'] = int(BlockchainNetwork.objects.get(id=data[idx]['blockchain_network']).chain_id)
                data[idx].pop('blockchain_network')

            response['data']['wallet_details'] = data
            response['message'] = GET_PROFILE_SUCCESS
            logger.info(response)
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response['data']['id'] = None
            response['message'] = PROFILE_DOES_NOT_EXIST
            response['error'] = str(e)
            logger.info(response)
            return Response(response, status=status.HTTP_200_OK)

    def post(self, request):
        response = dict(data=dict(), message="", error="")

        try:
            user_id = self.request.user.id
            request.data['user'] = user_id

            chain_id = request.data.get('chain_id', None)
            if chain_id is None:
                response['message'] = 'Please send Chain Id'
                return Response(response, status=status.HTTP_200_OK)
            blockchain_network_qs = BlockchainNetwork.objects.filter(chain_id=chain_id)
            if not blockchain_network_qs:
                response['message'] = 'No such chain_id or blockchain network found'
                return Response(response, status=status.HTTP_200_OK)
            request.data['blockchain_network'] = blockchain_network_qs[0].id

            serializer = self.serializer_class(data=request.data)

            if serializer.is_valid():
                serializer.save()
                data = serializer.data
                response['data']['user'] = user_id
                data.pop('id')
                data.pop('created_at')
                data.pop('modified_at')
                data.pop('user')
                data.pop('blockchain_network')
                response['data']['wallet_details'] = [data]
                response['data']['wallet_details'][0]['chain_id'] = request.data.get('chain_id')
                response['message'] = CREATE_USER_SMART_CONTRACT_WALLET_SUCCESS
                logger.info(response)
                return Response(response, status=status.HTTP_200_OK)
            response['message'] = CREATE_USER_SMART_CONTRACT_WALLET_FAIL
            response['error'] = serializer.errors
            logger.error(response['error'])
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            response['message'] = CREATE_USER_SMART_CONTRACT_WALLET_FAIL
            response['error'] = str(e)
            logger.info(response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        response = dict(data=dict(), message="Update will be enabled soon", error="")
        # user_id = self.request.user.id
        #
        # user_scw_obj = UserSmartContractWalletAddress.objects.filter(user_smart_contract_wallet_address=user_smart_contract_wallet_address)
        # serializer = self.serializer_class(profile_obj, data=request.data)
        #
        # if serializer.is_valid():
        #     # if 'phone_number' in request.data:
        #     #     user_obj.phone_number = request.data['phone_number']
        #     #     user_obj.save()
        #     serializer.save()
        #     data = serializer.data
        #     response['data'] = data
        #     # response['data']['phone_number'] = str(user_obj.phone_number)
        #     logger.info(response)
        #     return Response(response, status=status.HTTP_200_OK)
        # response['message'] = UPDATE_PROFILE_FAIL
        # response['error'] = serializer.errors
        # logger.error(response['error'])

        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        response = dict(data=dict(), message="Delete will be enabled soon", error="")
        # user_id = self.request.user.id
        # profile_obj = UserProfile.objects.get(user=user_id)
        # profile_obj.delete()
        # response['message'] = DELETE_PROFILE_SUCCESS
        # logger.info(response)
        return Response(response, status=status.HTTP_200_OK)
