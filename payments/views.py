from typing import Any, List

from rest_framework import generics, status, request
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from authentication.models import User
from api_keys.models import APIKey
from user_profile.models import UserProfile
from .models import (PaymentType, Currency, PaymentStatus, Payment,
                     PaymentSession, PurplePayFactoryContract, PaymentBurner,
                     PaymentBurnerAddress)
from .serializers import (
    PaymentTypeSerializer, CurrencySerializer, PaymentStatusSerializer,
    PaymentSerializer, PaymentSessionSerializer, PaymentBurnerSerializer,
    PaymentBurnerAddressSerializer, )
from .utils import *
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
import uuid
import datetime
from django.utils import timezone
import base64
from .apps import logger
from .resources.constants import (
    GET_PAYMENT_STATUS_SUCCESS, USER_ID_API_KEY_MISMATCH,
    CREATE_PAYMENT_SUCCESS, CREATE_PAYMENT_FAIL, EXCEPTION_OCCURRED,
    GET_PAYMENT_LIST_SUCCESS, GET_PAYMENT_SESSION_LIST_SUCCESS,
    CREATE_PAYMENT_SESSION_SUCCESS
)
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
from django.db.models import Q
import threading
import requests
import json
from copy import deepcopy

COINGECKO_EXCHANGE_RATE_1BTC_URL = "https://api.coingecko.com/api/v3/exchange_rates"


class PaymentTypeListCreate(generics.ListCreateAPIView):
    serializer_class = PaymentTypeSerializer
    queryset = PaymentType.objects.all()
    permission_classes = [IsAdminUser]


class PaymentTypeRetrieveUpdateDelete(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PaymentTypeSerializer
    queryset = PaymentType.objects.all()
    permission_classes = [IsAdminUser]
    lookup_field = "id"


class CurrencyListCreate(generics.ListCreateAPIView):
    serializer_class = CurrencySerializer
    queryset = Currency.objects.all()
    permission_classes = [IsAdminUser]


class CurrencyRetrieveUpdateDelete(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CurrencySerializer
    queryset = Currency.objects.all()
    permission_classes = [IsAdminUser]
    lookup_field = "id"


class PaymentStatusListCreate(generics.ListCreateAPIView):
    serializer_class = PaymentStatusSerializer
    queryset = PaymentStatus.objects.all()
    permission_classes = [IsAdminUser]


class PaymentStatusRetrieveUpdateDelete(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PaymentStatusSerializer
    queryset = PaymentStatus.objects.all()
    permission_classes = [IsAdminUser]
    lookup_field = "id"


class PaymentGetCreateUpdate(generics.GenericAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [AllowAny]

    def get(self, request):
        response = dict()
        response['message'] = ''
        response['error'] = 'GET method not allowed'
        response['data'] = []
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    # def get(self, request):
    #     response = dict()
    #
    #     try:
    #         # api_key = request.META.get('HTTP_X_API_KEY_LEGITT', 'No Header')
    #         api_key = request.data.get('api_key', None)
    #         # user_id = self.request.query_params.get('user')
    #         # print(request.query_params)
    #
    #         # Validate api_key and user_id
    #         api_key_in_db = APIKey.objects.filter(id=api_key)
    #         if len(api_key_in_db) == 0:
    #             return Response("No Payment Id found for this user", status=status.HTTP_200_OK)
    #         user_id_for_api_key_in_db = api_key_in_db[0].user.id
    #
    #         # if str(user_id) != str(user_id_for_api_key_in_db):
    #         #     return Response(USER_ID_API_KEY_MISMATCH,
    #         #                     status=status.HTTP_400_BAD_REQUEST)
    #
    #         queryset = Payment.objects.filter(user=user_id_for_api_key_in_db)
    #         serializer = self.serializer_class(queryset, many=True)
    #         data = serializer.data
    #
    #         response['data'] = data
    #         response['message'] = GET_PAYMENT_LIST_SUCCESS
    #         logger.info(response)
    #         return Response(response, status=status.HTTP_200_OK)
    #     except Exception as e:
    #         response['data'] = {}
    #         response['message'] = EXCEPTION_OCCURRED
    #         response['error'] = str(e)
    #         logger.info(response)
    #         return Response(response, status=status.HTTP_400_BAD_REQUEST)

    # @extend_schema(parameters=[
    #     OpenApiParameter(
    #         name='X-API-Key-Legitt',
    #         type=OpenApiTypes.UUID,
    #         location=OpenApiParameter.HEADER,
    #         description='API Key of the user',
    #         required=True
    #     )
    # ])
    def post(self, request):
        response = dict()
        api_key = request.data.get('api_key', None)

        # Validate api_key and user_id
        api_key_in_db = APIKey.objects.filter(id=api_key)
        if len(api_key_in_db) == 0:
            return Response("No Payment Id found for this User id", status=status.HTTP_200_OK)

        user_id_for_api_key_in_db = api_key_in_db[0].user.id
        user_profile = UserProfile.objects.filter(user=user_id_for_api_key_in_db)

        # if str(user_id) != str(user_id_for_api_key_in_db):
        #     return Response(USER_ID_API_KEY_MISMATCH, status=status.HTTP_400_BAD_REQUEST)
        request.data['user'] = user_id_for_api_key_in_db

        # address_to => change to burner smart contract

        # Get all tokens/currencies available in table
        currency_qs = Currency.objects.all()
        for currency_obj in currency_qs:
            chain_id = currency_obj.blockchain_network.chain_id
            currency = currency_obj.name
            symbol = currency_obj.symbol_primary
            token_address_on_network = currency_obj.token_address_on_network

        # create multiple addresses for each potential choice of token
        # Add a field to currency => map every token to its network and contract address
        # "asset": {
        #             "id": "1fc37950-768e-46e4-9658-98a8188723f3",
        #             "name": "USDT",
        #             "chainId": 80001,
        #             "address": "0xba569eae6fb2c233815174501b0e1210dc940b64",
        #             "currency": "usdt",
        #             "symbol": "USDT",
        #             "decimals": 6,
        #             "coingeckoId": "tether"
        #         }
        # "payment_tokens": [
        #     "usdc": {
        #               "token_address": "string",
        #               "burner_contract_address": "string",
        #               "amount": "int"
        #             },
        #     "usdt": {
        #               "token_address": "string",
        #               "burner_contract_address": "string",
        #               "amount": "int"
        #             },
        #     "matic": {
        #               "token_address": "string",
        #               "burner_contract_address": "string",
        #               "amount": "int"
        #             },
        # ]

        request.data['address_to'] = user_profile[0].user_smart_contract_wallet_address
        data = request.data
        serializer = self.serializer_class(data=data)

        if serializer.is_valid():
            serializer.save()
            data = serializer.data
            response['data'] = data
            response['message'] = CREATE_PAYMENT_SUCCESS
            logger.info(response)
            return Response(response, status=status.HTTP_200_OK)

        response['data'] = {}
        response['message'] = CREATE_PAYMENT_FAIL
        response['error'] = serializer.errors
        logger.error(response['error'])
        return Response(response, status=status.HTTP_400_BAD_REQUEST)


class PaymentSessionGetCreateUpdate(generics.GenericAPIView):
    serializer_class = PaymentSessionSerializer
    permission_classes = [AllowAny]

    @extend_schema(parameters=[
        # OpenApiParameter(
        #     name='X-API-Key-Legitt',
        #     type=OpenApiTypes.UUID,
        #     location=OpenApiParameter.HEADER,
        #     description='API Key of the user',
        #     required=True
        # ),
        # OpenApiParameter(
        #     name='user',
        #     type=OpenApiTypes.UUID,
        #     location=OpenApiParameter.QUERY,
        #     description='User Id',
        #     required=True
        # ),
        OpenApiParameter(
            name='payment_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.QUERY,
            description='Payment Id',
        )
    ])
    def get(self, request):
        response = dict()

        try:
            # api_key = request.META.get('HTTP_X_API_KEY_LEGITT', 'No Header')
            # user_id = self.request.query_params.get('user')
            api_key = request.data.get('api_key', None)

            # Validate api_key and user_id
            api_key_in_db = APIKey.objects.filter(id=api_key)
            if len(api_key_in_db) == 0:
                return Response("No Payment Id found for this User id", status=status.HTTP_200_OK)
            user_id_for_api_key_in_db = api_key_in_db[0].user.id

            # if str(user_id) != str(user_id_for_api_key_in_db):
            #     return Response(USER_ID_API_KEY_MISMATCH,
            #                     status=status.HTTP_400_BAD_REQUEST)

            payment_id = request.query_params.get('payment_id')

            if payment_id is None:
                payment_ids = Payment.objects.filter(user=user_id_for_api_key_in_db).values('id')
                queryset = PaymentSession.objects.filter(payment_id__in=payment_ids)
                serializer = self.serializer_class(queryset, many=True)
                data = serializer.data

                response['data'] = data
                response['message'] = GET_PAYMENT_SESSION_LIST_SUCCESS
                logger.info(response)
                return Response(response, status=status.HTTP_200_OK)

            else:  # user_id and specific payment_id specified - move to detail API

                queryset = PaymentSession.objects.filter(payment_id=payment_id)
                serializer = self.serializer_class(queryset, many=True)
                data = serializer.data

                response['data'] = data
                response['message'] = GET_PAYMENT_SESSION_LIST_SUCCESS
                logger.info(response)
                return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            response['data'] = {}
            response['message'] = EXCEPTION_OCCURRED
            response['error'] = str(e)
            logger.info(response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    # @extend_schema(parameters=[
    #     OpenApiParameter(
    #         name='X-API-Key-Legitt',
    #         type=OpenApiTypes.UUID,
    #         location=OpenApiParameter.HEADER,
    #         description='API Key of the user',
    #         required=True
    #     ),
    #     OpenApiParameter(
    #         name='user',
    #         type=OpenApiTypes.UUID,
    #         location=OpenApiParameter.QUERY,
    #         description='User Id',
    #         required=True
    #     )
    # ])
    def post(self, request):
        response = dict()
        # api_key = request.META.get('HTTP_X_API_KEY_LEGITT', 'No Header')
        # api_key = request.data.get('api_key', None)

        # user_id = self.request.query_params.get('user')

        # Validate api_key and user_id
        # api_key_in_db = APIKey.objects.filter(id=api_key)
        # if len(api_key_in_db) == 0:
        #     return Response("No API Key found", status=status.HTTP_400_BAD_REQUEST)

        # user_id_for_api_key_in_db = api_key_in_db[0].user.id

        # if str(user_id) != str(user_id_for_api_key_in_db):
        #     return Response(USER_ID_API_KEY_MISMATCH, status=status.HTTP_400_BAD_REQUEST)
        request.data['payment_status'] = '627cff96-c9d5-4e9e-8b28-c35ed607aa6f'  # In Progress
        data = request.data

        serializer = self.serializer_class(data=data)

        if serializer.is_valid():
            expires_at = timezone.now() + datetime.timedelta(hours=1)
            serializer.save(expires_at=expires_at)
            data = serializer.data
            response['data'] = data

            # Inject expires at
            response['message'] = CREATE_PAYMENT_SESSION_SUCCESS
            logger.info(response)
            return Response(response, status=status.HTTP_200_OK)

        response['data'] = {}
        response['message'] = CREATE_PAYMENT_FAIL
        response['error'] = serializer.errors
        logger.error(response['error'])
        return Response(response, status=status.HTTP_400_BAD_REQUEST)


class PaymentVerifyDetail(generics.GenericAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [AllowAny]

    def get(self, request, payment_id):
        response = dict()

        try:
            # session_id = request.query_params.get('session_id')
            if payment_id is None:
                response['data'] = {}
                response['message'] = "Please send payment_id"
                return Response(response, status=status.HTTP_200_OK)

            payment_qs = Payment.objects.filter(id=payment_id)
            # print(payment_qs)

            if len(payment_qs) == 0:
                response['data'] = {}
                response['message'] = "Invalid payment id."
                return Response(response, status=status.HTTP_200_OK)

            payment_obj = payment_qs[0]

            # Create GraphQL query
            url = "https://api.thegraph.com/subgraphs/name/abhikumar98/purple-pay-factory"

            # Select transport with url endpoint
            transport = AIOHTTPTransport(url=url)

            # create GraphQL client using defined transport
            client = Client(transport=transport, fetch_schema_from_transport=True)
            variable_values = {"paymentId": payment_id}

            # GraphQL query
            query = gql(
                """query ($paymentId: String!) { paymentRecieveds(where:{paymentId: $paymentId}){ paymentId merchantOrderId merchantWallet amount sender transactionHash} } """)
            # print('query:', query)
            # run query on transport
            result = client.execute(query, variable_values=variable_values)
            # print('query result: ', result)

            order_amount_to_be_paid = payment_obj.order_amount
            # print(f'order_amount_to_be_paid: {order_amount_to_be_paid}')

            amount_paid = 0.0
            for element in result.get('paymentRecieveds'):
                amount_paid += float(element.get('amount'))
            # print(f'amount_paid fetched from graphql: {amount_paid}')

            multiplication_factor_for_smallest_unit = 10 ** 18
            order_amount_to_be_paid_in_smallest_unit = order_amount_to_be_paid * multiplication_factor_for_smallest_unit

            # Database value => convert by multiplying with 10^18
            if amount_paid >= order_amount_to_be_paid_in_smallest_unit:
                payment_status_obj = PaymentStatus.objects.get(
                    name='Completed')  # '1046a834-8134-4be2-9dfd-48278b1d3383'    # completed'
                # print('Line 340: payment_status_completed', payment_status_obj)
            else:
                payment_status_obj = PaymentStatus.objects.get(
                    name='Partially Completed')  # 'b7ad5b34-96be-4ff3-bfbf-0a9097513744'    # completed'
                # print('Line 361: payment_status_partially_completed', payment_status_obj)

            payment_obj.payment_status = payment_status_obj
            # Sender
            address_from = ''
            transaction_hash = ''
            if len(result.get('paymentRecieveds', [])) >= 1:
                address_from = result.get('paymentRecieveds')[0].get('sender', '')
                transaction_hash = result.get('paymentRecieveds')[0].get('transactionHash', '')
            # ToDO: Add a column and write to database
            payment_obj.address_from = address_from
            payment_obj.transaction_hash = transaction_hash
            payment_obj.save()

            # Webhook - url called
            # Add webhook_url to user_details model + call from here

            serializer = self.serializer_class(payment_obj)
            # print(serializer.data)

            response['data'] = serializer.data
            response['data']['amount_paid'] = amount_paid / multiplication_factor_for_smallest_unit
            response['data']['remaining_amount'] = (
                                                           order_amount_to_be_paid_in_smallest_unit - amount_paid) / multiplication_factor_for_smallest_unit
            response['data']['transaction_hash'] = transaction_hash
            response['data']['payment_status_name'] = payment_status_obj.name
            response['message'] = 'Partial Payment completed. Please complete the payment.'
            response['error'] = ''
            # logger.info(response)

            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response['data'] = {}
            response['message'] = EXCEPTION_OCCURRED
            response['error'] = str(e)
            logger.info(response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class PaymentSessionGetDetail(generics.GenericAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [AllowAny]

    def get(self, request, session_id):
        response = dict()

        try:
            if session_id is None:
                response['data'] = {}
                response['message'] = "Please send session_id"
                return Response(response, status=status.HTTP_200_OK)

            payment_session_qs = PaymentSession.objects.filter(id=session_id)
            # print(payment_session_qs)

            if len(payment_session_qs) == 0:
                response['data'] = {}
                response['message'] = "Invalid session id. No payment id found for this session id"
                return Response(response, status=status.HTTP_200_OK)

            payment_session_obj = payment_session_qs[0]
            payment_instance_qs = Payment.objects.filter(id=payment_session_obj.payment_id.id)
            payment_instance_obj = payment_instance_qs[0]
            user_id = payment_instance_obj.user.id

            user_profile_instance_qs = UserProfile.objects.filter(user=user_id)
            user_smart_contract_wallet_address = user_profile_instance_qs[0].user_smart_contract_wallet_address

            # Create GraphQL query
            url = "https://api.thegraph.com/subgraphs/name/abhikumar98/purple-pay-factory"

            # Select transport with url endpoint
            transport = AIOHTTPTransport(url=url)

            # create GraphQL client using defined transport
            client = Client(transport=transport, fetch_schema_from_transport=True)

            variable_values = {
                "merchantWallet": user_smart_contract_wallet_address,
                "orderId": session_id
            }

            # GraphQL query
            query = gql(
                """query ($merchantWallet: Bytes, $orderId: String) { paymentRecieveds(where:{merchantWallet: $merchantWallet, orderId: $orderId}){ amount sender orderId merchantWallet } } """)
            # run query on transport
            result = client.execute(query, variable_values=variable_values)
            # print(result)

            order_amount_to_be_paid = payment_instance_obj.order_amount
            amount_paid = 0.0
            for element in result.get('paymentRecieveds'):
                amount_paid += float(element.get('amount'))
            user_order_id = payment_instance_obj.user_order_id

            response['data'] = {'amount_paid': amount_paid,
                                'order_amount_to_be_paid': order_amount_to_be_paid,
                                'address_to': user_smart_contract_wallet_address,
                                'session_id': session_id,
                                'user_order_id': user_order_id}
            response['message'] = 'Successfully completed payment'
            response['error'] = ''
            logger.info(response)
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response['data'] = {}
            response['message'] = EXCEPTION_OCCURRED
            response['error'] = str(e)
            logger.info(response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class PaymentList(generics.GenericAPIView):
    permission_classes = [IsAuthenticated | IsAdminUser, ]
    serializers = {
        'payment_burner': PaymentBurnerSerializer,
        'payment': PaymentSerializer,
    }
    default_serializer_class = PaymentBurnerSerializer

    def get_serializer_class(self, serializer_type):
        if serializer_type == 'payment':
            return self.serializers.get('payment')
        if serializer_type == 'payment_burner':
            return self.serializers.get('payment_burner')
        return self.default_serializer_class

    '''Receive API Key and return all payments for the given merchant'''

    def get(self, request):
        response = dict(data=[])
        try:
            user_id = self.request.user.id

            payment_qs_response = Payment.objects.filter(user=user_id)
            # print_statement_with_line('views', 535, 'payment_qs_response', payment_qs_response)
            payment_serializer = self.get_serializer_class('payment')

            # print_statement_with_line('views', 538, 'payment_qs_response', payment_qs_response)

            for element in payment_qs_response:
                payment_data = payment_serializer(element).data
                if element.currency is not None:
                    payment_data['symbol'] = element.currency.symbol_primary
                    payment_data['token_address'] = element.currency.token_address_on_network
                    payment_data['chain_id'] = element.currency.blockchain_network.chain_id
                    payment_data['chain_name'] = element.currency.blockchain_network.name
                    payment_data['decimals'] = element.currency.decimals
                    payment_data['image_url'] = element.currency.asset_url
                else:
                    payment_data['symbol'] = None
                    payment_data['token_address'] = None
                    payment_data['chain_id'] = None
                    payment_data['chain_name'] = None
                    payment_data['decimals'] = None
                    payment_data['image_url'] = None
                # payment_data.pop('created_at')
                # payment_data.pop('modified_at')
                payment_data.pop('currency')
                response['data'].append(payment_data)

            payment_burner_qs_response = PaymentBurner.objects.filter(user=user_id)
            payment_burner_serializer = self.get_serializer_class('payment_burner')

            for element in payment_burner_qs_response:
                # print(element, "::", element.currency.symbol_primary)
                payment_burner_data = payment_burner_serializer(element).data

                if element.currency is not None:
                    payment_burner_data['symbol'] = element.currency.symbol_primary
                    payment_burner_data['token_address'] = element.currency.token_address_on_network
                    payment_burner_data['chain_id'] = element.currency.blockchain_network.chain_id
                    payment_burner_data['chain_name'] = element.currency.blockchain_network.name
                    payment_burner_data['decimals'] = element.currency.decimals
                    payment_burner_data['image_url'] = element.currency.asset_url
                else:
                    payment_burner_data['symbol'] = None
                    payment_burner_data['token_address'] = None
                    payment_burner_data['chain_id'] = None
                    payment_burner_data['chain_name'] = None
                    payment_burner_data['decimals'] = None
                    payment_burner_data['image_url'] = None

                # payment_burner_data.pop('created_at')
                # payment_burner_data.pop('modified_at')
                payment_burner_data.pop('currency')
                response['data'].append(payment_burner_data)

            # Adding payment_status as string
            payment_status_all = PaymentStatus.objects.all()
            # print(payment_status_all)

            payment_status_all_name_set = {element.id: element.name for element in payment_status_all}
            # print(payment_status_all_name_set)

            for idx in range(len(response['data'])):
                response['data'][idx]['payment_status'] = payment_status_all_name_set.get(
                    response['data'][idx].get('payment_status', None), None)

            response['message'] = GET_PAYMENT_LIST_SUCCESS
            # print(response)
            # logger.info(response)
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            response['data'] = {}
            response['message'] = EXCEPTION_OCCURRED
            response['error'] = str(e)
            # logger.info(response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class PaymentFilter(generics.GenericAPIView):
    permission_classes = [IsAuthenticated | IsAdminUser, ]
    serializers = {
        'payment_burner': PaymentBurnerSerializer,
        'payment': PaymentSerializer,
    }
    default_serializer_class = PaymentBurnerSerializer

    def get_serializer_class(self, serializer_type):
        if serializer_type == 'payment':
            return self.serializers.get('payment')
        if serializer_type == 'payment_burner':
            return self.serializers.get('payment_burner')
        return self.default_serializer_class


    '''Receive API Key and return all payments for the given merchant
    https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior'''

    def process_str_to_date_obj(self, date_str, date_suffix, date_format):
        date_str_split = date_str.split('-')
        day_str = date_str_split[0]
        month_str = date_str_split[1]
        year_str = date_str_split[-1]
        date_str_complete = f'{year_str}-{month_str}-{day_str} {date_suffix}'
        # print(date_str_complete)
        date_obj_complete = datetime.datetime.strptime(date_str_complete, date_format)
        # print(date_obj_complete)
        return date_obj_complete

    def get(self, request):
        response = dict(data=[])
        try:
            start_date_str = request.query_params.get('start_date', '')  # Assuming senttime is 'DD-MM-YYYY'
            end_date_str = request.query_params.get('end_date', '')
            DATE_SUFFIX = '00:00:00.000000 +0000'
            DATE_FORMAT = '%Y-%m-%d %H:%M:%S.%f %z'

            # Case 1: Since start_date till today
            # Case 2: Between start_date and end_date
            # Case 3: Before start_Date

            # Case 2: Between start_date and end_date
            if not start_date_str or not end_date_str:
                response['data'] = []
                response['message'] = 'Please add missing date filter'
                response['error'] = ''
                return Response(response, status=status.HTTP_200_OK)

            start_date_obj = self.process_str_to_date_obj(start_date_str, DATE_SUFFIX, DATE_FORMAT)
            end_date_obj = self.process_str_to_date_obj(end_date_str, DATE_SUFFIX, DATE_FORMAT)
            user_id = self.request.user.id
            user_query = Q(user=user_id)
            # Get id for payment_status = completed
            payment_status_obj = PaymentStatus.objects.get(name='Completed')
            payment_status_query = Q(payment_status=payment_status_obj.id)
            date_query = Q(created_at__range=[start_date_obj, end_date_obj])

            #queryset = Payment.objects.filter(user_query & payment_status_query & date_query)
            # queryset = Payment.objects.filter(user_query)  # & payment_status_query & date_query)
            # print(queryset)
            # serializer = self.serializer_class(queryset, many=True)
            payment_qs_response = Payment.objects.filter(user_query & payment_status_query & date_query)
            # print_statement_with_line('views', 636, 'payment_qs_response', payment_qs_response)
            payment_serializer = self.get_serializer_class('payment')

            for element in payment_qs_response:
                payment_data = payment_serializer(element).data
                # print_statement_with_line('views', 640, 'payment_data', payment_data)
                payment_data['payment_status'] = 'Completed'
                if element.currency is not None:
                    payment_data['symbol'] = element.currency.symbol_primary
                    payment_data['token_address'] = element.currency.token_address_on_network
                    payment_data['chain_id'] = element.currency.blockchain_network.chain_id
                    payment_data['chain_name'] = element.currency.blockchain_network.name
                    payment_data['decimals'] = element.currency.decimals
                    payment_data['image_url'] = element.currency.asset_url
                else:
                    payment_data['symbol'] = None
                    payment_data['token_address'] = None
                    payment_data['chain_id'] = None
                    payment_data['chain_name'] = None
                    payment_data['decimals'] = None
                    payment_data['image_url'] = None
                # payment_data.pop('created_at')
                # payment_data.pop('modified_at')
                payment_data.pop('currency')
                response['data'].append(payment_data)
                # print_statement_with_line('views', 652, 'payment_data', payment_data)
                # print_statement_with_line('views', 652, 'response_data', response['data'])

            payment_burner_qs_response = PaymentBurner.objects.filter(user_query & payment_status_query & date_query)
            payment_burner_serializer = self.get_serializer_class('payment_burner')
            for element in payment_burner_qs_response:
                payment_burner_data = payment_burner_serializer(element).data
                payment_burner_data['payment_status'] = 'Completed'
                if element.currency is not None:
                    payment_burner_data['symbol'] = element.currency.symbol_primary
                    payment_burner_data['token_address'] = element.currency.token_address_on_network
                    payment_burner_data['chain_id'] = element.currency.blockchain_network.chain_id
                    payment_burner_data['chain_name'] = element.currency.blockchain_network.name
                    payment_burner_data['decimals'] = element.currency.decimals
                    payment_burner_data['image_url'] = element.currency.asset_url
                else:
                    payment_burner_data['symbol'] = None
                    payment_burner_data['token_address'] = None
                    payment_burner_data['chain_id'] = None
                    payment_burner_data['chain_name'] = None
                    payment_burner_data['decimals'] = None
                    payment_burner_data['image_url'] = None

                # payment_burner_data.pop('created_at')
                # payment_burner_data.pop('modified_at')
                payment_burner_data.pop('currency')
                response['data'].append(payment_burner_data)

            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            response['data'] = {}
            response['message'] = EXCEPTION_OCCURRED
            response['error'] = str(e)
            # logger.info(response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class PaymentBurnerGetCreateUpdate(generics.GenericAPIView):
    serializer_class = PaymentBurnerSerializer
    permission_classes = [AllowAny]

    def get(self, request):
        response = dict()

        try:
            api_key = request.query_params.get('api_key', None)
            # print(request.query_params)

            # Validate api_key and user_id
            api_key_in_db = APIKey.objects.filter(id=api_key)
            if len(api_key_in_db) == 0:
                return Response("No Payment Id found for this user", status=status.HTTP_200_OK)
            user_id_for_api_key_in_db = api_key_in_db[0].user.id

            # if str(user_id) != str(user_id_for_api_key_in_db):
            #     return Response(USER_ID_API_KEY_MISMATCH,
            #                     status=status.HTTP_400_BAD_REQUEST)

            queryset = Payment.objects.filter(user=user_id_for_api_key_in_db)
            serializer = self.serializer_class(queryset, many=True)
            data = serializer.data

            response['data'] = data
            response['message'] = GET_PAYMENT_LIST_SUCCESS
            # logger.info(response)
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            response['data'] = {}
            response['message'] = EXCEPTION_OCCURRED
            response['error'] = str(e)
            # logger.info(response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        response = dict()
        # api_key = request.META.get('HTTP_X_API_KEY_LEGITT', 'No Header')
        # user_id = self.request.data.get('user')
        api_key = request.data.get('api_key', None)
        # print(api_key)

        # Validate api_key and user_id
        api_key_in_db = APIKey.objects.filter(id=api_key)
        if len(api_key_in_db) == 0:
            return Response("No Payment Id found for this User id", status=status.HTTP_200_OK)

        user_id_for_api_key_in_db = api_key_in_db[0].user.id
        user_profile = UserProfile.objects.filter(user=user_id_for_api_key_in_db)

        # if str(user_id) != str(user_id_for_api_key_in_db):
        #     return Response(USER_ID_API_KEY_MISMATCH, status=status.HTTP_400_BAD_REQUEST)
        request.data['user'] = user_id_for_api_key_in_db
        request.data['final_address_to'] = user_profile[0].user_smart_contract_wallet_address
        data = request.data
        serializer = self.serializer_class(data=data)

        if serializer.is_valid():
            serializer.save()
            data = serializer.data
            response['data'] = data
            response['message'] = CREATE_PAYMENT_SUCCESS
            # logger.info(response)
            return Response(response, status=status.HTTP_200_OK)

        response['data'] = {}
        response['message'] = CREATE_PAYMENT_FAIL
        response['error'] = serializer.errors
        # logger.error(response['error'])
        return Response(response, status=status.HTTP_400_BAD_REQUEST)


class PaymentBurnerAddressGetCreateUpdate(generics.GenericAPIView):
    serializers = {
        'payment': PaymentBurnerSerializer,
        'payment_burner_address': PaymentBurnerAddressSerializer,
    }
    default_serializer_class = PaymentBurnerAddressSerializer
    permission_classes = [AllowAny]

    def get_serializer_class(self, serializer_type):
        if serializer_type == 'payment':
            return self.serializers.get('payment')
        if serializer_type == 'payment_burner_address':
            return self.serializers.get('payment_burner_address')
        return self.default_serializer_class

    def post(self, request):
        response = dict(data={"tokens": []}, message="")
        api_key = request.data.get('api_key', None)

        # Validate api_key and user_id
        api_key_in_db = APIKey.objects.filter(id=api_key)
        # print(f"api_key_in_db: ${api_key_in_db}")
        if len(api_key_in_db) == 0:
            return Response("No such API Key found!", status=status.HTTP_200_OK)

        user_id_for_api_key_in_db = api_key_in_db[0].user.id
        user_profile = UserProfile.objects.filter(user=user_id_for_api_key_in_db)

        request.data['user'] = user_id_for_api_key_in_db

        ## Add a filter depending on network requested from frontend
        request.data['final_address_to'] = user_profile[0].user_smart_contract_wallet_address
        request.data['currency'] = Currency.objects.get(symbol_primary=request.data.get('currency', 'usd').upper()).id

        payment_status_in_progress = PaymentStatus.objects.get(name='In Progress')

        request.data['payment_status'] = payment_status_in_progress.id

        chain_id = request.data.get('chain_id', '137')
        request.data['initial_block_number'] = get_latest_block_number(chain_id)
        payment_serializer = self.get_serializer_class('payment')(data=request.data)
        if payment_serializer.is_valid():
            payment_serializer.save()

        payment_id = str(payment_serializer.data.get('id', None))
        # print('560', payment_id)

        # All tokens

        all_currencies_qs = Currency.objects.exclude(currency_type__name='Fiat')
        # print_statement_with_line('views', '726', 'all_currencies_qs', all_currencies_qs)

        # amount_in_that_token
        order_amount = payment_serializer.data.get('order_amount', None)  # in Dollar
        # 100 US Dollar
        # Which api
        exchange_rates = json.loads(requests.get(COINGECKO_EXCHANGE_RATE_1BTC_URL).text).get('rates', {})
        exchange_rate_usd_per_btc = exchange_rates.get('usd', None)

        # merchant final scw address
        user_id_for_api_key_in_db = api_key_in_db[0].user.id
        user_profile = UserProfile.objects.filter(user=user_id_for_api_key_in_db)
        user_scw_final_address_to = user_profile[0].user_smart_contract_wallet_address

        # purple_pay_multisig_address - defined above
        payment_status_in_progress = PaymentStatus.objects.get(name='In Progress')
        payment_status_completed = PaymentStatus.objects.get(name='Completed')

        for currency in all_currencies_qs:
            currency_chain_id = currency.blockchain_network.chain_id
            purple_pay_factory_contract_address_qs = PurplePayFactoryContract.objects.filter(
                blockchain_network=currency.blockchain_network.id)
            if not purple_pay_factory_contract_address_qs:
                continue
            # print(f'purple_pay_factory_contract_address: {purple_pay_factory_contract_address_qs}')
            currency_network_name = currency.blockchain_network.name
            currency_token_address = currency.token_address_on_network

            if currency.symbol_primary.lower() in ['usdc', 'usdt']:
                exchange_rate_current_currency_per_btc = exchange_rate_usd_per_btc
            else:
                exchange_rate_current_currency_per_btc = exchange_rates.get(currency.coingecko_id)
            if exchange_rate_current_currency_per_btc is None:
                continue
            amount_in_current_currency = order_amount * (
                    exchange_rate_current_currency_per_btc.get('value', None) / exchange_rate_usd_per_btc.get(
                'value', None))
            amount_in_current_currency_as_smallest_unit = int(amount_in_current_currency * (10 ** currency.decimals))
            # print('603', amount_in_current_currency_as_smallest_unit)
            contract = create_contract_instance(purple_pay_factory_contract_address_qs[0].address,
                                                purple_pay_factory_contract_address_qs[0].contract_abi)
            burner_contract_address = get_burner_contract_address(
                contract, payment_id, currency_token_address, amount_in_current_currency_as_smallest_unit,
                user_scw_final_address_to,
                purple_pay_multisig_address)  # ToDo - maintain a mapping of merchant SCW to network

            data = {
                "payment_id": payment_id,
                "currency": currency.id,
                "burner_address": burner_contract_address,
                "order_amount": amount_in_current_currency,
                "payment_status": PaymentStatus.objects.get(name="In Progress").id,
                "is_used_for_payment": False
            }

            burner_address_serializer = self.get_serializer_class('payment_burner_address')(data=data)
            # print("*" * 50)
            # print(f'burner_address_serializer::{burner_address_serializer}')
            # print("*" * 50)
            # serializer = burner_serializer
            if burner_address_serializer.is_valid():
                burner_address_serializer.save()
                response_element = burner_address_serializer.data
                response_element.pop('currency', None)
                response_element.pop('id', None)
                response_element.pop('created_at', None)
                response_element.pop('modified_at', None)
                response_element.pop('payment_status', None)
                response_element.pop('payment_id', None)
                append_to_response = {
                    'symbol': currency.symbol_primary,
                    'token_address': currency_token_address,
                    'chain_id': currency_chain_id,
                    'chain_name': currency_network_name,
                    'decimals': currency.decimals,
                    'image_url': currency.asset_url
                }
                response_element.update(append_to_response)
                # print(f'response_element_final: {response_element}')
                response['data']['tokens'].append(response_element)

        response['data']['id'] = payment_id
        response['data']['payment_status'] = payment_status_in_progress.name

        response['message'] = "Burner Addresses Created Successfully"
        # logger.info(response)
        return Response(response, status=status.HTTP_200_OK)

        # response['data'] = {}
        # response['message'] = CREATE_PAYMENT_FAIL
        # response['error'] = serializer.errors
        # # logger.error(response['error'])
        # return Response(response, status=status.HTTP_400_BAD_REQUEST)


class PaymentBurnerAddressVerifyDetail(generics.GenericAPIView):
    serializers = {
        'payment': PaymentBurnerSerializer,
        'payment_burner_address': PaymentBurnerAddressSerializer,
    }
    default_serializer_class = PaymentBurnerAddressSerializer
    permission_classes = [AllowAny]

    def get_serializer_class(self, serializer_type):
        if serializer_type == 'payment':
            return self.serializers.get('payment')
        if serializer_type == 'payment_burner_address':
            return self.serializers.get('payment_burner_address')
        return self.default_serializer_class

    def get(self, request, payment_id):
        response = dict(data={})
        try:
            if payment_id is None:
                response['data'] = {}
                response['message'] = "Please send payment_id"
                return Response(response, status=status.HTTP_200_OK)

            payment_burner_address_qs = PaymentBurnerAddress.objects.filter(payment_id=payment_id)
            print(f'line 838 :: payment_burner_address_qs :: {payment_burner_address_qs}')

            if len(payment_burner_address_qs) == 0:
                response['data'] = {}
                response['message'] = "Invalid payment id."
                return Response(response, status=status.HTTP_200_OK)

            payment_status_in_progress = PaymentStatus.objects.get(name='In Progress')
            payment_status_completed = PaymentStatus.objects.get(name='Completed')

            payment_burner_obj = PaymentBurner.objects.get(id=payment_id)
            # print_statement_with_line('views', '849', 'payment_burner_obj', payment_burner_obj)

            payment_burner_address_serializer = {}
            payment_burner_address_obj_used_for_payment = None
            token_instance = {}
            payment_burner_data_for_response = {}
            burner_address = ''

            payment_completed_flag = False

            # Fetch balance for each address
            for payment_burner_address_obj in payment_burner_address_qs:
                burner_address = payment_burner_address_obj.burner_address
                token_instance = payment_burner_address_obj.currency
                # print_statement_with_line('views', '870', 'token name', token_instance.name)

                # print_statement_with_line('views', '872', 'payment_burner_address_obj', payment_burner_address_obj)
                # fetch balance of given address

                if token_instance.currency_type.name.lower() == 'native':
                    amount_in_burner_address = get_burner_address_balance_native(burner_address)
                    print('line 871 native', amount_in_burner_address)
                else:
                    amount_in_burner_address = get_burner_address_balance(burner_address, token_instance,
                                                                          erc20_token_abi)
                    # print('869', 'amount_in_burner_address', amount_in_burner_address)

                # address_from = get_address_from(burner_address)
                print('*' * 100, "::" * 50)
                print('order_amount in geth::::', payment_burner_address_obj.order_amount * (
                        10 ** token_instance.decimals))
                if payment_burner_address_obj.order_amount * (
                        10 ** token_instance.decimals) <= amount_in_burner_address:
                    payment_completed_flag = True
                    print('at line 886::', "payment_completed_flag", payment_completed_flag, burner_address,
                          token_instance)
                    payment_burner_address_update_data = {"is_used_for_payment": True,
                                                          "payment_status": payment_status_completed.id}
                    payment_burner_address_serializer = self.get_serializer_class('payment_burner_address')(
                        payment_burner_address_obj,
                        data=payment_burner_address_update_data, partial=True)
                    # print('line 676', payment_burner_address_serializer.initial_data)
                    if payment_burner_address_serializer.is_valid():
                        payment_burner_address_serializer.save()
                        payment_burner_address_obj_used_for_payment = payment_burner_address_serializer.data
                        # print_statement_with_line('views', 889, 'payment_burner_address_obj_used_for_payment', payment_burner_address_obj_used_for_payment)

                    # Update Payment Burner Object Id
                    # payment_burner_obj = PaymentBurner.objects.get(id=payment_id)
                    payment_burner_update_data = {
                        "address_from": "",  # ToDo - address_from + transaction_hash
                        "burner_address_to": burner_address,
                        "currency": payment_burner_address_obj.currency.id,
                        "payment_status": payment_status_completed.id
                    }

                    payment_burner_serializer = self.get_serializer_class('payment')(
                        payment_burner_obj, data=payment_burner_update_data, partial=True)
                    # print_statement_with_line('views', 908, 'payment_burner_serializer', payment_burner_serializer)
                    if payment_burner_serializer.is_valid():
                        # print_statement_with_line('views', 909, 'payment_burner_serializer', payment_burner_serializer)
                        payment_burner_serializer.save()
                        payment_burner_data_for_response = payment_burner_serializer.data
                    break

            if not payment_completed_flag:
                payment_burner_address_qs_response = PaymentBurnerAddress.objects.filter(payment_id=payment_id)
                tokens_for_response = []
                for element in payment_burner_address_qs_response:
                    token = {}
                    token['burner_address'] = element.burner_address
                    token['order_amount'] = element.order_amount
                    token['is_used_for_payment'] = element.is_used_for_payment
                    token['symbol'] = element.currency.symbol_primary
                    token['token_address'] = element.currency.token_address_on_network
                    token['chain_id'] = element.currency.blockchain_network.chain_id
                    token['chain_name'] = element.currency.blockchain_network.name
                    token['decimals'] = element.currency.decimals
                    token['image_url'] = element.currency.asset_url
                    tokens_for_response.append(token)

                # payment_burner_addresses = PaymentBurnerAddress.objects.filter(payment_id=payment_id)
                # payment_burner_addresses_serializer = self.get_serializer_class('payment_burner_address')(payment_burner_addresses, many=True)
                response['data']['id'] = payment_id
                response['data']['payment_details'] = {}
                response['data']['tokens'] = tokens_for_response
                response['payment_status'] = payment_status_in_progress.name
                response['message'] = ['Payment In Progress']
                return Response(response)

            # Get Transaction hash
            start_block = payment_burner_obj.initial_block_number
            chain_id = request.data.get('chain_id', '137')
            current_block_number = get_latest_block_number(chain_id)

            block_idx = start_block
            transaction_hashes = []

            purple_pay_factory_contract_obj = PurplePayFactoryContract.objects.get(
                blockchain_network=token_instance.blockchain_network)

            t = threading.Thread(target=deploy_and_disburse, args=(), kwargs={
                'burner_address_instance': payment_burner_address_serializer.data,
                'token_instance': token_instance,
                'payment_instance': payment_burner_data_for_response,
                'purple_pay_contract_instance': purple_pay_factory_contract_obj
            })
            t.setDaemon(True)
            t.start()

            payment_burner_address_qs_response = PaymentBurnerAddress.objects.filter(payment_id=payment_id)
            tokens_for_response = []
            for element in payment_burner_address_qs_response:
                token = {}
                token['burner_address'] = element.burner_address
                token['order_amount'] = element.order_amount
                token['is_used_for_payment'] = element.is_used_for_payment
                token['symbol'] = element.currency.symbol_primary
                token['token_address'] = element.currency.token_address_on_network
                token['chain_id'] = element.currency.blockchain_network.chain_id
                token['chain_name'] = element.currency.blockchain_network.name
                token['decimals'] = element.currency.decimals
                token['image_url'] = element.currency.asset_url
                tokens_for_response.append(token)

            # payment_burner_address_qs_response_serialised = self.get_serializer_class('payment_burner_address')(
            #     payment_burner_address_qs_response, many=True)

            # print('line 986', payment_burner_data_for_response)
            response['data']['payment_details'] = payment_burner_data_for_response  # payment_burner_serializer.data
            payment_burner_data_for_response.pop('id')
            payment_burner_data_for_response.pop('created_at')
            payment_burner_data_for_response.pop('modified_at')
            payment_burner_data_for_response.pop('user')
            currency = Currency.objects.get(id=payment_burner_data_for_response['currency'])

            payment_burner_data_for_response['token'] = currency.name
            payment_burner_data_for_response['symbol'] = currency.symbol_primary
            payment_burner_data_for_response['token_address'] = currency.token_address_on_network
            payment_burner_data_for_response['chain_name'] = currency.blockchain_network.name
            payment_burner_data_for_response['chain_id'] = currency.blockchain_network.chain_id
            payment_burner_data_for_response['token_type'] = currency.currency_type.name
            payment_burner_data_for_response['decimals'] = currency.decimals
            payment_burner_data_for_response['image_url'] = currency.asset_url
            response['data']['payment_status'] = payment_status_completed.name
            # response['data']['payment_status_id'] = payment_status_completed.id
            # payment_burner_address_qs_response_serialised.data
            response['data']['id'] = payment_id
            response['data']['tokens'] = tokens_for_response  # payment_burner_address_qs_response_serialised.data
            response['message'] = ['Payment Completed']
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response['data'] = {}
            response['message'] = EXCEPTION_OCCURRED
            response['error'] = str(e)
            # logger.info(response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class PaymentBurnerAddressVerifyDetail3(generics.GenericAPIView):
    serializers = {
        'payment': PaymentBurnerSerializer,
        'payment_burner_address': PaymentBurnerAddressSerializer,
    }
    default_serializer_class = PaymentBurnerAddressSerializer
    permission_classes = [AllowAny]

    def get_serializer_class(self, serializer_type):
        if serializer_type == 'payment':
            return self.serializers.get('payment')
        if serializer_type == 'payment_burner_address':
            return self.serializers.get('payment_burner_address')
        return self.default_serializer_class

    def get(self, request, payment_id):
        response = dict(data={})
        try:
            if payment_id is None:
                response['data'] = {}
                response['message'] = "Please send payment_id"
                return Response(response, status=status.HTTP_200_OK)

            chain_id = request.data.get('chain_id', '137')

            payment_burner_address_qs = PaymentBurnerAddress.objects.filter(payment_id=payment_id)
            print(f'line 838 :: payment_burner_address_qs :: {payment_burner_address_qs}')

            if len(payment_burner_address_qs) == 0:
                response['data'] = {}
                response['message'] = "No Burner Addresses available against this payment Id"
                return Response(response, status=status.HTTP_200_OK)

            payment_status_in_progress = PaymentStatus.objects.get(name='In Progress')
            payment_status_completed = PaymentStatus.objects.get(name='Completed')

            payment_burner_obj = PaymentBurner.objects.get(id=payment_id)
            # print_statement_with_line('views', '849', 'payment_burner_obj', payment_burner_obj)

            payment_completed_in_burner_address_flag = False
            payment_burner_address_true_qs = PaymentBurnerAddress.objects.filter(payment_id=payment_id).filter(
                is_used_for_payment=True)

            ####### First call - payment not made to any address yet
            if len(payment_burner_address_true_qs) == 0:  # No payment made yet
                # payment_burner_address_qs = PaymentBurnerAddress.objects.filter(payment_id=payment_id)
                for payment_burner_address_obj in payment_burner_address_qs:
                    burner_address = payment_burner_address_obj.burner_address
                    token_instance = payment_burner_address_obj.currency
                    token_type = token_instance.currency_type.name.lower()
                    token_address = token_instance.token_address_on_network

                    # fetch balance of given address
                    if token_instance.currency_type.name.lower() == 'native':
                        amount_in_burner_address = get_burner_address_balance_native(burner_address)
                    else:
                        amount_in_burner_address = get_burner_address_balance(burner_address, token_instance,
                                                                              erc20_token_abi)

                    if payment_burner_address_obj.order_amount * (
                            10 ** token_instance.decimals) <= amount_in_burner_address:
                        payment_completed_in_burner_address_flag = True

                        # The specific payment_burner_address of burner_address table
                        # for the given payment Id is updated
                        payment_burner_address_update_data = {"is_used_for_payment": True,
                                                              "payment_status": payment_status_completed.id}
                        payment_burner_address_serializer = self.get_serializer_class('payment_burner_address')(
                            payment_burner_address_obj,
                            data=payment_burner_address_update_data, partial=True)

                        if payment_burner_address_serializer.is_valid():
                            # print_statement_with_line('views', 1357, 'payment_burner_address_serializer',
                            #                           payment_burner_address_serializer)
                            payment_burner_address_serializer.save()

                        # Update payment_burner object for the given payment_id
                        # Need to fetch transaction_hash for the payment made

                        if token_type == 'native':
                            burner_address_transaction_details = get_transaction_details_using_block_explorer(
                                burner_address, chain_id)
                        else:
                            burner_address_transaction_details = get_transaction_details_using_block_explorer_erc20(
                                burner_address, token_address, chain_id)
                        print('views', 1364, 'burner_address_transaction_details', burner_address_transaction_details)

                        payment_burner_transaction_details_update_data = {}
                        if burner_address_transaction_details:
                            tx_details_obj = burner_address_transaction_details[0]
                            # print_statement_with_line('views', 1368, 'tx_details_obj', tx_details_obj)
                            payment_burner_transaction_details_update_data['address_from'] = tx_details_obj.get('from',
                                                                                                                None)
                            payment_burner_transaction_details_update_data['transaction_hash'] = tx_details_obj.get(
                                'hash', None)
                            payment_burner_transaction_details_update_data[
                                'transaction_block_number'] = tx_details_obj.get('blockNumber', None)
                            payment_burner_transaction_details_update_data[
                                'transaction_block_hash'] = tx_details_obj.get('blockHash', None)

                        # Update specific payment burner for the queries payment_id
                        payment_burner_update_data = {
                            "burner_address_to": burner_address,
                            "currency": payment_burner_address_obj.currency.id,
                            "payment_status": payment_status_completed.id
                        }
                        # Combine both information - received from etherscan + local
                        payment_burner_update_data.update(payment_burner_transaction_details_update_data)

                        print('views', 1387, 'payment_burner_update_data', payment_burner_update_data)
                        payment_burner_serializer = self.get_serializer_class('payment')(
                            payment_burner_obj, data=payment_burner_update_data, partial=True)

                        if payment_burner_serializer.is_valid():
                            payment_burner_serializer.save()
                            payment_burner_data_for_response = payment_burner_serializer.data
                            print('views', '1392', 'payment_burner_data_for_response', payment_burner_data_for_response)
                        else:
                            payment_burner_data_for_response = {}
                        # start thread to deploy and disburse
                        payment_burner_data_for_response_copy = deepcopy(payment_burner_data_for_response)
                        kwarg_dict = dict(
                            burner_address_instance=payment_burner_address_serializer.data,
                            token_instance=token_instance,
                            payment_instance=payment_burner_data_for_response_copy
                        )
                        # print_statement_with_line('views', 1524, 'kwarg_dict', kwarg_dict)

                        if payment_burner_address_obj.burner_contract_deploy_status == 'not deploy':
                            start_thread_to_deploy_and_disburse(deploy_and_disburse, kwarg_dict)

                        if payment_burner_address_obj.burner_contract_deploy_status == 'failure deploy':
                            start_thread_to_deploy_and_disburse(deploy_and_disburse, kwarg_dict)

                        # Remove unnecessary keys from response
                        keys_to_remove = ['id', 'created_at', 'modified_at', 'user']
                        for key in keys_to_remove:
                            payment_burner_data_for_response.pop(key, None)

                        currency = Currency.objects.get(id=payment_burner_data_for_response['currency'])
                        payment_burner_data_for_response['token'] = currency.name
                        payment_burner_data_for_response['symbol'] = currency.symbol_primary
                        payment_burner_data_for_response['token_address'] = currency.token_address_on_network
                        payment_burner_data_for_response['chain_name'] = currency.blockchain_network.name
                        payment_burner_data_for_response['chain_id'] = currency.blockchain_network.chain_id
                        payment_burner_data_for_response['token_type'] = currency.currency_type.name
                        payment_burner_data_for_response['decimals'] = currency.decimals
                        payment_burner_data_for_response['image_url'] = currency.asset_url
                        payment_burner_data_for_response['payment_status'] = payment_status_completed.name

                        tokens_for_response = []
                        payment_burner_address_qs_updated = PaymentBurnerAddress.objects.filter(payment_id=payment_id)
                        for element in payment_burner_address_qs_updated:
                            token = dict()
                            token['burner_address'] = element.burner_address
                            token['order_amount'] = element.order_amount
                            token['is_used_for_payment'] = element.is_used_for_payment
                            token['symbol'] = element.currency.symbol_primary
                            token['token_address'] = element.currency.token_address_on_network
                            token['chain_id'] = element.currency.blockchain_network.chain_id
                            token['chain_name'] = element.currency.blockchain_network.name
                            token['decimals'] = element.currency.decimals
                            token['image_url'] = element.currency.asset_url
                            token[
                                "transfer_to_merchant_transaction_hash"] = element.transfer_to_merchant_transaction_hash
                            token["burner_contract_deploy_status"] = element.burner_contract_deploy_status
                            token[
                                "burner_contract_deploy_failure_reason"] = element.burner_contract_deploy_failure_reason
                            tokens_for_response.append(token)

                        response['data'][
                            'payment_details'] = payment_burner_data_for_response  # payment_burner_serializer.data
                        response['data']['payment_status'] = payment_status_completed.name
                        response['data']['id'] = payment_id
                        response['data'][
                            'tokens'] = tokens_for_response  # payment_burner_address_qs_response_serialised.data
                        response['message'] = ['Payment Completed']
                        # print_statement_with_line('views', 1444, 'response', response)
                        return Response(response, status=status.HTTP_200_OK)

                if not payment_completed_in_burner_address_flag:

                    # here return response of payment in progress - payment_burner_address_qs + payment_id + in_progress
                    tokens_for_response = []
                    for element in payment_burner_address_qs:
                        token = dict()
                        token['burner_address'] = element.burner_address
                        token['order_amount'] = element.order_amount
                        token['is_used_for_payment'] = element.is_used_for_payment
                        token['symbol'] = element.currency.symbol_primary
                        token['token_address'] = element.currency.token_address_on_network
                        token['chain_id'] = element.currency.blockchain_network.chain_id
                        token['chain_name'] = element.currency.blockchain_network.name
                        token['decimals'] = element.currency.decimals
                        token['image_url'] = element.currency.asset_url
                        token["transfer_to_merchant_transaction_hash"] = element.transfer_to_merchant_transaction_hash
                        token["burner_contract_deploy_status"] = element.burner_contract_deploy_status
                        token["burner_contract_deploy_failure_reason"] = element.burner_contract_deploy_failure_reason
                        tokens_for_response.append(token)

                    response['data']['id'] = payment_id
                    response['data']['payment_details'] = {}
                    response['data']['tokens'] = tokens_for_response
                    response['payment_status'] = payment_status_in_progress.name
                    response['message'] = [payment_status_in_progress.name]
                    return Response(response)

            ####### Later calls once payment made and one of the burner addresses is True
            if payment_burner_address_true_qs:
                print('completed 1470')

                # Check for transaction hash - due to etherscan latency

                if payment_burner_obj.transaction_hash is None:
                    # Need to fetch transaction_hash for the payment made
                    burner_address = payment_burner_obj.burner_address_to
                    payment_burner_address_true_obj = payment_burner_address_true_qs[0]
                    token_instance = payment_burner_address_true_obj.currency
                    token_type = token_instance.currency_type.name.lower()
                    token_address = token_instance.token_address_on_network

                    if token_type == 'native':
                        burner_address_transaction_details = get_transaction_details_using_block_explorer(
                            burner_address, chain_id)
                    else:
                        burner_address_transaction_details = get_transaction_details_using_block_explorer_erc20(
                            burner_address, token_address, chain_id)
                    print('views', 1630, 'burner_address_transaction_details', burner_address_transaction_details)

                    payment_burner_transaction_details_update_data = {}
                    if burner_address_transaction_details:
                        tx_details_obj = burner_address_transaction_details[0]
                        print_statement_with_line('views', 1368, 'tx_details_obj', tx_details_obj)
                        payment_burner_transaction_details_update_data['address_from'] = tx_details_obj.get('from',
                                                                                                            None)
                        payment_burner_transaction_details_update_data['transaction_hash'] = tx_details_obj.get(
                            'hash', None)
                        payment_burner_transaction_details_update_data[
                            'transaction_block_number'] = tx_details_obj.get('blockNumber', None)
                        payment_burner_transaction_details_update_data[
                            'transaction_block_hash'] = tx_details_obj.get('blockHash', None)

                    payment_burner_serializer = self.get_serializer_class('payment')(
                        payment_burner_obj, data=payment_burner_transaction_details_update_data, partial=True)

                    if payment_burner_serializer.is_valid():
                        payment_burner_serializer.save()
                        payment_burner_data_for_response = payment_burner_serializer.data
                        print('views', '1392', 'payment_burner_data_for_response', payment_burner_data_for_response)
                    else:
                        payment_burner_serializer = self.get_serializer_class('payment')(payment_burner_obj)
                        payment_burner_data_for_response = payment_burner_serializer.data

                else:

                    payment_burner_serializer = self.get_serializer_class('payment')(payment_burner_obj)
                    payment_burner_data_for_response = payment_burner_serializer.data

                print('line 1475', payment_burner_data_for_response)
                # start thread to deploy and disburse
                payment_burner_address_true_obj = payment_burner_address_true_qs[0]
                payment_burner_address_serializer = self.get_serializer_class('payment_burner_address')(
                    payment_burner_address_true_obj)
                token_instance = payment_burner_address_true_obj.currency

                print_statement_with_line('views', 1518, 'payment_burner_data_for_response',
                                          payment_burner_data_for_response)
                payment_burner_data_for_response_copy = deepcopy(payment_burner_data_for_response)
                kwarg_dict = dict(
                    burner_address_instance=payment_burner_address_serializer.data,
                    token_instance=token_instance,
                    payment_instance=payment_burner_data_for_response_copy
                )
                # print_statement_with_line('views', 1524, 'kwarg_dict',
                #                           kwarg_dict)
                # print_statement_with_line('views', 1543,
                #                           'payment_burner_address_true_obj.burner_contract_deploy_status',
                #                           payment_burner_address_true_obj.burner_contract_deploy_status)
                if (payment_burner_address_true_obj.burner_contract_deploy_status == 'not deploy'
                        or payment_burner_address_true_obj.burner_contract_deploy_status == 'failure deploy'):
                    start_thread_to_deploy_and_disburse(deploy_and_disburse, kwarg_dict)

                # Remove unnecessary keys from response
                keys_to_remove = ['id', 'created_at', 'modified_at', 'user']
                for key in keys_to_remove:
                    payment_burner_data_for_response.pop(key, None)

                currency = Currency.objects.get(id=payment_burner_data_for_response['currency'])
                payment_burner_data_for_response['token'] = currency.name
                payment_burner_data_for_response['symbol'] = currency.symbol_primary
                payment_burner_data_for_response['token_address'] = currency.token_address_on_network
                payment_burner_data_for_response['chain_name'] = currency.blockchain_network.name
                payment_burner_data_for_response['chain_id'] = currency.blockchain_network.chain_id
                payment_burner_data_for_response['token_type'] = currency.currency_type.name
                payment_burner_data_for_response['decimals'] = currency.decimals
                payment_burner_data_for_response['image_url'] = currency.asset_url
                payment_burner_data_for_response['payment_status'] = payment_status_completed.name

                tokens_for_response = []
                for element in payment_burner_address_qs:
                    token = dict()
                    token['burner_address'] = element.burner_address
                    token['order_amount'] = element.order_amount
                    token['is_used_for_payment'] = element.is_used_for_payment
                    token['symbol'] = element.currency.symbol_primary
                    token['token_address'] = element.currency.token_address_on_network
                    token['chain_id'] = element.currency.blockchain_network.chain_id
                    token['chain_name'] = element.currency.blockchain_network.name
                    token['decimals'] = element.currency.decimals
                    token['image_url'] = element.currency.asset_url
                    token["transfer_to_merchant_transaction_hash"] = element.transfer_to_merchant_transaction_hash
                    token["burner_contract_deploy_status"] = element.burner_contract_deploy_status
                    token["burner_contract_deploy_failure_reason"] = element.burner_contract_deploy_failure_reason
                    tokens_for_response.append(token)

                response['data']['id'] = payment_id
                response['data']['payment_details'] = payment_burner_data_for_response
                response['data']['tokens'] = tokens_for_response
                response['payment_status'] = payment_status_completed.name
                response['message'] = [payment_status_completed.name]
                return Response(response, status=status.HTTP_200_OK)

                # here return response - payment_burner_address_qs + payment_burner_obj + payment_id
                # check status of contract deployment + deploy and disburse if not done

        except Exception as e:
            print(e)
            response['data']['id'] = payment_id
            response['data']['payment_details'] = {}
            response['data']['tokens'] = []
            response['payment_status'] = None
            response['message'] = str(e)
            return Response(response, status=status.HTTP_200_OK)

            # here return response - payment_burner_address_qs + payment_burner_obj + payment_id

    #     if payment_burner_address_true_qs:
    #
    #
    # except Exception as e:
    # print(e)


class PaymentBurnerList(generics.GenericAPIView):
    serializer_class = PaymentBurnerSerializer
    permission_classes = [IsAuthenticated | IsAdminUser, ]

    '''Receive API Key and return all payments for the given merchant'''

    def get(self, request):
        response = dict()
        try:
            user_id = self.request.user.id
            queryset = PaymentBurner.objects.filter(user=user_id)
            serializer = self.serializer_class(queryset, many=True)
            data = serializer.data
            response['data'] = data
            # Adding payment_status as string
            payment_status_all = PaymentStatus.objects.all()
            # print(payment_status_all)

            payment_status_all_name_set = {element.id: element.name for element in payment_status_all}
            # print(payment_status_all_name_set)

            for idx in range(len(response['data'])):
                response['data'][idx]['payment_status_name'] = payment_status_all_name_set.get(
                    response['data'][idx].get('payment_status', None), None)

            response['message'] = GET_PAYMENT_LIST_SUCCESS
            # print(response)
            # logger.info(response)
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            response['data'] = {}
            response['message'] = EXCEPTION_OCCURRED
            response['error'] = str(e)
            # logger.info(response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
