from rest_framework import generics, status, request
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from authentication.models import User
from .models import UserProfile, UserType, UserSmartContractWalletAddress, Webhook, WebhookActivity
from payments.models import BlockchainNetwork, Currency
from .serializers import (UserProfileSerializer, UserTypeSerializer, UserSmartContractWalletAddressSerializer,
                          WebhookSerializer, WebhookActivitySerializer)
import uuid
import datetime
from django.utils import timezone
import base64
from user_profile.apps import logger
from user_profile.resources.constants import (
    PROFILE_DOES_NOT_EXIST, GET_PROFILE_SUCCESS, CREATE_PROFILE_FAIL,
    UPDATE_PROFILE_FAIL, DELETE_PROFILE_SUCCESS, DELETE_PROFILE_FAIL,
    CREATE_USER_SMART_CONTRACT_WALLET_SUCCESS, CREATE_USER_SMART_CONTRACT_WALLET_FAIL,
    WEBHOOK_URL_STATUS, WEBHOOK_EVENT_TYPE
)
from commons.utils import generate_secret_for_webhook


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
            print(request.data)

            # user_obj = User.objects.get(id=user_id)
            # user_obj = User.objects.get(id=user_id)
            if not request.data['first_name'] or request.data['first_name'] is None:
                response["message"] = "First Name is missing"
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            if not request.data['last_name'] or request.data['last_name'] is None:
                response["message"] = "Last Name is missing"
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            if not request.data['location'] or request.data['location'] is None:
                response["message"] = "Location is missing"
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            if not request.data['company'] or request.data['company'] is None:
                response["message"] = "Company is missing"
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            if not request.data['default_network'] or request.data['default_network'] is None:
                response["message"] = "Default Network is missing"
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            blockchain_qs = BlockchainNetwork.objects.filter(chain_id=request.data['default_network'])
            default_network_chain_id = request.data['default_network']
            if not blockchain_qs:
                response["message"] = "Default Network is Invalid"
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            request.data['default_network'] = blockchain_qs[0].id
            serializer = self.serializer_class(data=request.data)

            if serializer.is_valid():
                # if 'phone_number' in request.data:
                #     user_obj.phone_number = request.data['phone_number']
                #     user_obj.save()
                serializer.save()

                data = serializer.data
                data['default_network'] = int(default_network_chain_id)
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
            response['data']['id'] = None
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
            response['data']['id'] = None
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
            response['data']['id'] = None
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


class WebhookGetCreateUpdate(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WebhookSerializer

    def get(self, request):
        """
        Handles GET requests for webhook urls.
        It retrieves data for a given user_id from JWT and returns an appropriate response.

        :param request: -
        :param args: -
        :param kwargs: -
        :return: A Response object containing the response data.
        The structure of the response is the following:
         {
            "data": {
                "webhook_list": [
                    {
                        'id': "303v58e2-1388-411c-a3f9-2662de0716d1",
                        'user': "30b658e2-1388-a3f9-411c-266d2e0716d1",
                        'createdAt': "2023-08-10T14:24:15.782737Z",
                        'modifiedAt': "2023-08-10T14:24:15.782737Z",
                        'url': "https://URL",
                        'status': "ACTIVE",
                        'secretKey': "w9r49792797",
                        'eventType': "SUCCESS",
                        'description': "This is a sample response for webhooks list for a given user id",
                        'metadata': ""
                    }
                ]
            },
            "message": "Successfully fetched",
            "error": ""
        }

        """
        response = dict(data=dict(), message="", error="")

        try:
            user_id = self.request.user.id
            webhook_qs = Webhook.objects.filter(user=user_id)
            serializer = self.serializer_class(webhook_qs, many=True)
            response_data = list()
            for element in serializer.data:
                data = dict()
                data['id'] = element.get('id', None)
                data['user'] = element.get('user', None)
                data['createdAt'] = element.get('created_at', None)
                data['modifiedAt'] = element.get('modified_at', None)
                data['url'] = element.get('url', None)
                data['status'] = element.get('status', None)
                data['secretKey'] = element.get('secret_key', None)
                data['eventType'] = element.get('event_type', None)
                data['description'] = element.get('description', None)
                data['metadata'] = element.get('metadata', None)

                response_data.append(data)
            print(response_data)
            response['data'] = {
                'webhookList': response_data
            }
            response['message'] = "Successfully fetched webhooks for the given user"
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            response['message'] = 'Unable to fetch webhooks for the given user'
            response['error'] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        """
        :param request:
        {
            'url': "https://URL",
            'status': "ACTIVE",
            'eventType': "SUCCESS",
            'description': "This is a sample request for webhooks list for a given user id",
            'metadata': ""
        }

        :return:
        {
            'id': "303v58e2-1388-411c-a3f9-2662de0716d1",
            'user': "30b658e2-1388-a3f9-411c-266d2e0716d1",
            'createdAt': "2023-08-10T14:24:15.782737Z",
            'modifiedAt': "2023-08-10T14:24:15.782737Z",
            'url': "https://URL",
            'status': "ACTIVE",
            'secretKey': "w9r49792797",
            'eventType': "SUCCESS",
            'description': "This is a sample response for webhooks list for a given user id",
            'metadata': ""
        }
        """
        response = dict(data=dict(), message="", error="")
        request_data = dict()
        print(self.request.data)

        try:
            user_id = self.request.user.id

            request_data['event_type'] = request.data.get('eventType', None)
            if request_data['event_type'] and request_data['event_type'] not in WEBHOOK_EVENT_TYPE:
                response["error"] = "Webhook event type is invalid!"
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            if request_data['event_type'] == 'SUCCESS':
                webhook_qs_success = Webhook.objects.filter(event_type='SUCCESS')
                if len(webhook_qs_success) >= 2:
                    response["error"] = "You have crossed the limit for webhooks for a successful payment!"
                    return Response(response, status=status.HTTP_400_BAD_REQUEST)
            elif request_data['event_type'] == 'FAIL':
                webhook_qs_fail = Webhook.objects.filter(event_type='FAIL')
                if len(webhook_qs_fail) >= 2:
                    response["error"] = "You have crossed the limit for webhooks for a failed payment!"
                    return Response(response, status=status.HTTP_400_BAD_REQUEST)

            request_data['status'] = request.data.get('status', None)
            if request_data['status'] and request_data['status'] not in WEBHOOK_URL_STATUS:
                response["error"] = "Webhook status is invalid!"
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            request_data['user'] = user_id
            request_data['url'] = request.data.get('url', None)
            secret_key = generate_secret_for_webhook()
            request_data['description'] = request.data.get('description', None)

            webhook_serializer = self.serializer_class(data=request_data)
            if webhook_serializer.is_valid():
                webhook_serializer.validated_data['secret_key'] = secret_key
                webhook_serializer.save()
                response_data = dict()
                response_data['id'] = webhook_serializer.data.get('id', None)
                response_data['user'] = webhook_serializer.data.get('user', None)
                response_data['createdAt'] = webhook_serializer.data.get('created_at', None)
                response_data['modifiedAt'] = webhook_serializer.data.get('modified_at', None)
                response_data['url'] = webhook_serializer.data.get('url', None)
                response_data['status'] = webhook_serializer.data.get('status', None)
                response_data['secretKey'] = webhook_serializer.data.get('secret_key', None)
                response_data['eventType'] = webhook_serializer.data.get('event_type', None)
                response_data['description'] = webhook_serializer.data.get('description', None)
                response_data['metadata'] = webhook_serializer.data.get('metadata', None)

                print(response_data)
                response['data'] = {
                    'webhook': response_data
                }
                response['message'] = 'Webhook has been successfully created'
                return Response(response, status=status.HTTP_200_OK)
            else:
                errors = webhook_serializer.errors
                response['message'] = "Webhook creation has failed"
                response['error'] = errors
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            response['message'] = "Webhook creation has failed"
            response['error'] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        response = dict(data=dict(), message="", error="")

        try:
            user_id = self.request.user.id
            webhook_id = self.request.data.get('id', None)
            request_data = dict()
            print('request_data: ', request_data)
            if not webhook_id:
                response['error'] = 'Webhook Id is Missing'
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            webhook_qs = Webhook.objects.filter(user=user_id).filter(id=webhook_id)

            if len(webhook_qs) == 0:
                response['error'] = 'Webhook Id is invalid!'
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            if 'eventType' in self.request.data:
                request_data['event_type'] = request.data.get('eventType', None)
                if request_data['event_type'] not in WEBHOOK_EVENT_TYPE:
                    response["error"] = "Webhook event type is invalid!"
                    return Response(response, status=status.HTTP_400_BAD_REQUEST)
                if request_data['event_type'] == 'SUCCESS':
                    webhook_qs_success = Webhook.objects.filter(user=user_id).filter(event_type='SUCCESS')
                    if len(webhook_qs_success) >= 2:
                        response[
                            "error"] = "You have crossed the limit for webhooks for a successful payment! Edit one of them!"
                        return Response(response, status=status.HTTP_400_BAD_REQUEST)
                elif request_data['event_type'] == 'FAIL':
                    webhook_qs_fail = Webhook.objects.filter(event_type='FAIL')
                    if len(webhook_qs_fail) >= 2:
                        response[
                            "error"] = "You have crossed the limit for webhooks for a failed payment! Edit one of them"
                        return Response(response, status=status.HTTP_400_BAD_REQUEST)

            if 'status' in self.request.data:
                request_data['status'] = self.request.data.get('status', None)
                if request_data['status'] not in WEBHOOK_URL_STATUS:
                    response["error"] = "Webhook status is invalid!"
                    return Response(response, status=status.HTTP_400_BAD_REQUEST)

            request_data['user'] = user_id

            if 'url' in self.request.data:
                request_data['url'] = self.request.data.get('url', None)
            if 'secretKey' in self.request.data:
                request_data['secret_key'] = self.request.data.get('secretKey', None)
            if 'description' in self.request.data:
                request_data['description'] = self.request.data.get('description', None)

            webhook_obj = webhook_qs[0]
            webhook_serializer = self.serializer_class(webhook_obj, data=request_data,
                                                       partial=True)
            if webhook_serializer.is_valid():
                webhook_serializer.save()
                response_data = dict()
                response_data['id'] = webhook_serializer.data.get('id', None)
                response_data['user'] = webhook_serializer.data.get('user', None)
                response_data['createdAt'] = webhook_serializer.data.get('created_at', None)
                response_data['modifiedAt'] = webhook_serializer.data.get('modified_at', None)
                response_data['url'] = webhook_serializer.data.get('url', None)
                response_data['status'] = webhook_serializer.data.get('status', None)
                response_data['secretKey'] = webhook_serializer.data.get('secret_key', None)
                response_data['eventType'] = webhook_serializer.data.get('event_type', None)
                response_data['description'] = webhook_serializer.data.get('description', None)
                response_data['metadata'] = webhook_serializer.data.get('metadata', None)

                print(response_data)
                response['data'] = {
                    'webhook': response_data
                }
                response['message'] = 'Successfully updated the given webhook'
                return Response(response, status=status.HTTP_200_OK)
            else:
                errors = webhook_serializer.errors
                print(errors)
                response['data'] = self.request.data
                response['message'] = 'Failed to updated the given webhook'
                response['error'] = errors
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            response['message'] = 'Failed to updated the given webhook'
            response['error'] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class WebhookDelete(generics.DestroyAPIView):

    def delete(self, request, *args, **kwargs):
        response = dict(data=dict(), message="", error="")

        try:
            webhook_id = self.kwargs.get('webhookId', None)
            print('KWARG:', self.kwargs)
            if not webhook_id:
                response['error'] = 'Webhook id is missing or invalid'
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            user_id = self.request.user.id
            webhook_qs = Webhook.objects.filter(user=user_id).filter(id=webhook_id)
            if webhook_qs:
                webhook_obj = webhook_qs[0]
                webhook_obj.delete()

                response['data'] = {'webhookId': webhook_id}
                response['message'] = f'{webhook_id} has been deleted'
                return Response(response, status=status.HTTP_200_OK)
            else:
                response['data'] = {}
                response['error'] = 'Webhook not found for the given id'
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            response['data'] = {}
            response['message'] = 'Could not delete the webhook id'
            response['error'] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class WebhookActivityGetCreateUpdate(generics.GenericAPIView):
    def get(self, request):
        return Response({})

    def post(self, request):
        return Response({})

    def delete(self, request):
        return Response({})
