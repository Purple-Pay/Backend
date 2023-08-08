from typing import Any, List
from rest_framework import generics, status, request
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from authentication.models import User
from api_keys.models import APIKey
from user_profile.models import UserProfile
from .models import (PaymentType, Currency, PaymentStatus, Payment,
                     PaymentSession, PurplePayFactoryContract, PaymentBurner,
                     PaymentBurnerAddress, BlockchainNetwork, PaymentBurnerSample,
                     PaymentBurnerAddressSample)
from .serializers import (
    PaymentTypeSerializer, CurrencySerializer, PaymentStatusSerializer,
    PaymentSerializer, PaymentSessionSerializer, PaymentBurnerSerializer,
    PaymentBurnerAddressSerializer, PaymentBurnerSampleSerializer,
    PaymentBurnerAddressSampleSerializer)
from .utils import *
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
import uuid
import datetime
from django.utils import timezone
import base64
from .apps import logger
import os
from .resources.constants import (
    GET_PAYMENT_STATUS_SUCCESS, USER_ID_API_KEY_MISMATCH,
    CREATE_PAYMENT_SUCCESS, CREATE_PAYMENT_FAIL, EXCEPTION_OCCURRED,
    GET_PAYMENT_LIST_SUCCESS, GET_PAYMENT_SESSION_LIST_SUCCESS,
    CREATE_PAYMENT_SESSION_SUCCESS, COINGECKO_EXCHANGE_RATE_1BTC_URL,
    COINGECKO_EXCHANGE_RATE_VS_1USD_URL, PAYMENT_ID_NOT_FOUND_FAIL, DATE_FILTER_MISSING_FAIL,
    PURPLE_PAY_FACTORY_CONTRACT_UNAVAILABLE, CREATE_BURNER_ADDRESS_SUCCESS, CREATE_BURNER_ADDRESS_FAIL,
    PAYMENT_COMPLETED_SUCCESS, BURNER_ADDRESS_UNAVAILABLE_AGAINST_PAYMENT_ID_FAIL, PAYMENT_STATUS_COMPLETED,
    PAYMENT_STATUS_IN_PROGRESS, PAYMENT_ID_MISSING_FAIL, DEPLOY_STATUS_NOT_DEPLOY, DEPLOY_STATUS_FAILURE_DEPLOY,
    MAINNET, TESTNET, PAYMENT_TYPES, DEVICE_TYPES, OS_TYPES, USDOLLAR, PAYMENT_TYPES_MAPPING, CHAIN_IDS,
    PAYMENT_TYPES_DB_TO_ENUM_MAPPING
)
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
from django.db.models import Q
import threading
import requests
import json
from copy import deepcopy


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


def get_chain_ids_by_env():
    deployed_env = os.environ.get('BUILD_ENV', 'dev')
    testnet_qs = BlockchainNetwork.objects.filter(network_type__name=TESTNET)
    chain_ids = [element.chain_id for element in testnet_qs]
    if deployed_env == 'sit':
        mainnet_qs = BlockchainNetwork.objects.filter(network_type__name=MAINNET)
        chain_ids = [element.chain_id for element in mainnet_qs]
        return chain_ids, MAINNET
    if deployed_env == 'prod':
        mainnet_qs = BlockchainNetwork.objects.filter(network_type=MAINNET)
        chain_ids = [element.chain_id for element in mainnet_qs]
        return chain_ids, MAINNET
    return chain_ids, TESTNET


class ChainConfigGet(generics.GenericAPIView):
    permission_classes = [AllowAny, ]

    def get(self, request):
        """Return all chain details for the given environment"""
        response = dict(data=dict(chain_details=[]), message="", error="")
        try:
            deployed_env = os.environ.get('BUILD_ENV', 'dev')
            if deployed_env == 'dev':
                chain_qs = BlockchainNetwork.objects.filter(network_type__name=TESTNET).filter(is_active=True)
                testnet = True
            else:
                chain_qs = BlockchainNetwork.objects.filter(network_type__name=MAINNET).filter(is_active=True)
                testnet = False

            for chain_obj in chain_qs:
                response_obj = dict()

                response_obj['id'] = int(chain_obj.chain_id)
                response_obj['name'] = chain_obj.name
                response_obj['network'] = chain_obj.network
                response_obj['nativeCurrency'] = dict()

                native_currency_qs = chain_obj.currencies.filter(currency_type__name='Native')
                if native_currency_qs:
                    native_currency_obj = native_currency_qs[0]
                    response_obj['nativeCurrency'] = dict(name=native_currency_obj.name,
                                                          symbol=native_currency_obj.symbol_primary,
                                                          decimals=native_currency_obj.decimals
                                                          )
                response_obj['rpcUrls'] = {}
                response_obj['blockExplorers'] = {}
                if chain_obj.rpc_default is not None:
                    rpc_default = chain_obj.rpc_default.url

                    rpc_public_qs = chain_obj.rpc_public.all()
                    rpc_public_urls = [element.url for element in rpc_public_qs]

                    response_obj['rpcUrls'] = {
                        'default': {'http': [rpc_default]},
                        'public': {'http': rpc_public_urls}
                    }
                if chain_obj.blockexplorer_default is not None:
                    response_obj['blockExplorers'] = {
                        'default': {
                            'name': chain_obj.blockexplorer_default.name,
                            'url': chain_obj.blockexplorer_default.url
                        }
                    }

                response_obj['testnet'] = testnet
                response['data']['chain_details'].append(response_obj)
            response['message'] = 'Successfully fetched chain details'
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response['message'] = 'Could not fetch chain details'
            response['error'] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class PaymentConfig(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def get(self):
        """
        :return: {
        chains_supported: {
        'testnet': [{chain_id: '81', name: 'Shibuya'}, {chain_id: '80001', name: 'Mumbai'}],
        'mainnet': []
        },
        payment_type: [ecommerce, one time payment, scan and pay, p2p],
        currency: ['usd'],
        device_metadata: {
        "env": {
        "device_type": ["app, web, others, wap"],
        "os_type": ["ios, android, windows, linux, others"],
    },
        }
        }

        """
        response = dict(data=dict(chains_supported=list(), device_metadata=dict()), message="", error="")
        try:
            chain_qs = BlockchainNetwork.objects.filter(is_active=True).filter(
                Q(network_type__name=TESTNET) | Q(network_type__name=MAINNET))
            for chain_obj in chain_qs:
                response_obj = dict()
                response_obj['id'] = int(chain_obj.chain_id)
                response_obj['name'] = chain_obj.name
                response['data']['chains_supported'].append(response_obj)

            response['data']['payment_type'] = PAYMENT_TYPES
            response['data']['currency'] = USDOLLAR
            response['data']['device_metadata'] = {
                'env': {
                    'device_type': DEVICE_TYPES,
                    'os_type': OS_TYPES,
                }
            }
            response['message'] = 'Successfully fetched supported payment configuration values'
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response['message'] = 'Unable to fetch supported payment configurations'
            response['error'] = str(e)
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

    def get(self, request):
        """Receive API Key and return all payments for the given merchant"""

        response = dict(data=[], message="", error="")
        try:
            user_id = self.request.user.id

            payment_qs_response = Payment.objects.filter(user=user_id)
            # print_statement_with_line('views', 535, 'payment_qs_response', payment_qs_response)
            payment_serializer = self.get_serializer_class('payment')
            # print_statement_with_line('views', 538, 'payment_qs_response', payment_qs_response)

            for element in payment_qs_response:
                payment_data = payment_serializer(element).data
                payment_data['payment_type'] = PAYMENT_TYPES_DB_TO_ENUM_MAPPING[element.payment_type.name]

                if element.currency is not None:
                    payment_data['symbol'] = element.currency.symbol_primary
                    payment_data['token_address'] = element.currency.token_address_on_network
                    # payment_data['chain_id'] = element.currency.blockchain_network.chain_id
                    # payment_data['chain_name'] = element.currency.blockchain_network.name
                    payment_data['decimals'] = element.currency.decimals
                    payment_data['image_url'] = element.currency.asset_url
                else:
                    payment_data['symbol'] = None
                    payment_data['token_address'] = None
                    # payment_data['chain_id'] = None
                    # payment_data['chain_name'] = None
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
                payment_burner_data['payment_type'] = PAYMENT_TYPES_DB_TO_ENUM_MAPPING[element.payment_type.name]

                if element.currency is not None:
                    payment_burner_data['symbol'] = element.currency.symbol_primary
                    payment_burner_data['token_address'] = element.currency.token_address_on_network
                    # payment_burner_data['chain_id'] = element.currency.blockchain_network.chain_id
                    # payment_burner_data['chain_name'] = element.currency.blockchain_network.name
                    payment_burner_data['decimals'] = element.currency.decimals
                    payment_burner_data['image_url'] = element.currency.asset_url
                else:
                    payment_burner_data['symbol'] = None
                    payment_burner_data['token_address'] = None
                    # payment_burner_data['chain_id'] = None
                    # payment_burner_data['chain_name'] = None
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

            blockchain_network_all = BlockchainNetwork.objects.all()
            blockchain_network_all_name_set = {element.id: element.chain_id for element in blockchain_network_all}
            # print("lines 173", blockchain_network_all_name_set)

            for idx in range(len(response['data'])):
                response['data'][idx]['chain_id'] = blockchain_network_all_name_set.get(
                    response['data'][idx].get('blockchain_network', None), None)
                if "blockchain_network" in response['data'][idx]:
                    response['data'][idx].pop('blockchain_network')
                # print("line 178", response['data'][idx])

            chain_ids_for_env, network_type = get_chain_ids_by_env()
            result = []
            for idx in range(len(response['data'])):
                if response['data'][idx]['chain_id'] in chain_ids_for_env:
                    result.append(response['data'][idx])

            # print("response::", response)
            response['data'] = result
            response['network_type'] = network_type
            response['message'] = GET_PAYMENT_LIST_SUCCESS
            # print(response)
            # logger.info(response)
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            response['data'] = []
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

    def process_str_to_date_obj(self, date_str, date_suffix, date_format):
        """
        Receive API Key and return all payments for the given merchant
        https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
        """

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
        response = dict(data=[], message="", error="")
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
                response['message'] = DATE_FILTER_MISSING_FAIL
                return Response(response, status=status.HTTP_200_OK)

            start_date_obj = self.process_str_to_date_obj(start_date_str, DATE_SUFFIX, DATE_FORMAT)
            end_date_obj = self.process_str_to_date_obj(end_date_str, DATE_SUFFIX, DATE_FORMAT)
            user_id = self.request.user.id
            user_query = Q(user=user_id)
            # Get id for payment_status = completed
            payment_status_obj = PaymentStatus.objects.get(name=PAYMENT_STATUS_COMPLETED)
            payment_status_query = Q(payment_status=payment_status_obj.id)
            date_query = Q(created_at__range=[start_date_obj, end_date_obj])

            payment_qs_response = Payment.objects.filter(user_query & payment_status_query & date_query)
            # print_statement_with_line('views', 636, 'payment_qs_response', payment_qs_response)
            payment_serializer = self.get_serializer_class('payment')

            for element in payment_qs_response:
                payment_data = payment_serializer(element).data
                payment_data['payment_type'] = PAYMENT_TYPES_DB_TO_ENUM_MAPPING[element.payment_type.name]
                # print_statement_with_line('views', 640, 'payment_data', payment_data)
                payment_data['payment_status'] = PAYMENT_STATUS_COMPLETED
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
                payment_burner_data['payment_status'] = PAYMENT_STATUS_COMPLETED
                payment_burner_data['payment_type'] = PAYMENT_TYPES_DB_TO_ENUM_MAPPING[element.payment_type.name]
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
            response['message'] = EXCEPTION_OCCURRED
            response['error'] = str(e)
            # logger.info(response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


# Currently in Use: 24 May 2023 | Uses create_contract_instance and get_burner_contract_address
class PaymentBurnerAddressGetCreateUpdate3(generics.GenericAPIView):
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
        response = dict(data={"tokens": list()}, message="", error="")

        try:
            api_key = request.data.get('api_key', None)

            # Validate api_key and user_id
            api_key_in_db = APIKey.objects.filter(id=api_key)
            # print(f"api_key_in_db: ${api_key_in_db}")
            if len(api_key_in_db) == 0:
                return Response("No such API Key found!", status=status.HTTP_200_OK)

            user_id_for_api_key_in_db = api_key_in_db[0].user.id
            user_profile = UserProfile.objects.filter(user=user_id_for_api_key_in_db)

            request_payment_type = request.data.get('payment_type', 'na')
            print(request.data)
            print('REQUEST PAYMENT TYPE: ', request_payment_type)
            if request_payment_type not in PAYMENT_TYPES_MAPPING:
                request_payment_type = 'na'
            payment_type = PAYMENT_TYPES_MAPPING[request_payment_type]
            print('REQUEST PAYMENT TYPE after check invalid: ', request_payment_type, "::", payment_type)

            payment_type_id = PaymentType.objects.filter(name=payment_type)[0].id
            print(payment_type_id)
            request.data['payment_type'] = payment_type_id
            request.data['user'] = user_id_for_api_key_in_db
            request.data['final_address_to'] = user_profile[0].user_smart_contract_wallet_address
            request.data['currency'] = Currency.objects.get(
                symbol_primary=request.data.get('currency', 'usd').upper()).id

            payment_status_in_progress = PaymentStatus.objects.get(name=PAYMENT_STATUS_IN_PROGRESS)
            request.data['payment_status'] = payment_status_in_progress.id

            ## Add a filter depending on network requested from frontend - 137/Polygon Mainnet as default
            chain_id = str(request.data.get('chain_id', '137'))
            if chain_id not in CHAIN_IDS:
                response['message'] = 'This chain is not supported! We are working on it!'
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            print_statement_with_line('views', '1208', 'chain_id', chain_id)

            blockchain_network = BlockchainNetwork.objects.get(chain_id=chain_id)
            # print('blockchain_network::::', blockchain_network)
            print_statement_with_line('views', '1069', 'blockchain_network', blockchain_network)
            request.data['blockchain_network'] = blockchain_network.id
            request.data['initial_block_number'] = get_latest_block_number(chain_id)
            print_statement_with_line('views', '1072', 'request_data', request.data)
            payment_serializer = self.get_serializer_class('payment')(data=request.data)
            if payment_serializer.is_valid():
                payment_serializer.save()

            payment_id = str(payment_serializer.data.get('id', None))
            description = str(payment_serializer.data.get('description', None))
            # all currencies qs for requested network
            all_currencies_qs = Currency.objects.exclude(currency_type__name='Fiat').filter(
                blockchain_network=blockchain_network.id)

            print_statement_with_line('views', '1084', 'all_currencies_qs', all_currencies_qs)
            #
            # amount_in_that_token
            order_amount = payment_serializer.data.get('order_amount', None)  # in Dollar
            # 100 US Dollar
            # Which api
            exchange_rates = json.loads(requests.get(COINGECKO_EXCHANGE_RATE_1BTC_URL).text).get('rates', {})
            exchange_rate_usd_per_btc = exchange_rates.get('usd', None)

            # merchant final scw address
            # user_id_for_api_key_in_db = api_key_in_db[0].user.id
            # user_profile = UserProfile.objects.filter(user=user_id_for_api_key_in_db)
            user_scw_final_address_to = user_profile[0].user_smart_contract_wallet_address

            # purple_pay_multisig_address - defined above
            payment_status_in_progress = PaymentStatus.objects.get(name=PAYMENT_STATUS_IN_PROGRESS)
            payment_status_completed = PaymentStatus.objects.get(name=PAYMENT_STATUS_COMPLETED)

            purple_pay_factory_contract_address_qs = PurplePayFactoryContract.objects.filter(
                blockchain_network=blockchain_network.id)
            print_statement_with_line('views', '1105', 'purple_pay_factory_contract_address_qs',
                                      purple_pay_factory_contract_address_qs)
            if not purple_pay_factory_contract_address_qs:
                response['message'] = PURPLE_PAY_FACTORY_CONTRACT_UNAVAILABLE
                return Response(response, status=status.HTTP_200_OK)

            # Extract coingecko_id
            coingecko_ids = [element.coingecko_id for element in all_currencies_qs]
            coingecko_ids_string = ",".join(coingecko_ids)
            exchange_rates_vs_1usd_url = f"{COINGECKO_EXCHANGE_RATE_VS_1USD_URL}?ids={coingecko_ids_string}&vs_currencies=usd"
            exchange_rates_vs_1usd_res = json.loads(requests.get(exchange_rates_vs_1usd_url).text)
            for currency in all_currencies_qs:
                print_statement_with_line('views', '1110', 'currency',
                                          currency)
                currency_chain_id = currency.blockchain_network.chain_id
                # purple_pay_factory_contract_address_qs = PurplePayFactoryContract.objects.filter(
                #     blockchain_network=currency.blockchain_network.id)
                # if not purple_pay_factory_contract_address_qs:
                #     continue
                # print(f'purple_pay_factory_contract_address: {purple_pay_factory_contract_address_qs}')
                currency_network_name = currency.blockchain_network.name
                currency_token_address = currency.token_address_on_network

                # if currency.symbol_primary.lower() in ['usdc', 'usdt']:
                #     exchange_rate_current_currency_per_btc = exchange_rate_usd_per_btc
                # else:
                #     exchange_rate_current_currency_per_btc = exchange_rates.get(currency.coingecko_id)
                # if exchange_rate_current_currency_per_btc is None:
                #     continue
                exchange_rate_current_currency_per_usd = exchange_rates_vs_1usd_res.get(currency.coingecko_id,
                                                                                        {'usd': None}).get('usd', None)
                if exchange_rate_current_currency_per_usd is None:
                    continue
                if currency.currency_type.name == 'Native':
                    amount_in_current_currency = round(order_amount / exchange_rate_current_currency_per_usd, 18)
                else:
                    amount_in_current_currency = round(order_amount / exchange_rate_current_currency_per_usd, 6)
                amount_in_current_currency_as_smallest_unit = int(
                    amount_in_current_currency * (10 ** currency.decimals))
                # print('520', amount_in_current_currency, "::::", order_amount / exchange_rate_current_currency_per_usd)
                # print('603', amount_in_current_currency_as_smallest_unit)
                print_statement_with_line('views', '1130', 'purple_pay_factory_contract_address_qs[0].address',
                                          purple_pay_factory_contract_address_qs[0].address)
                print_statement_with_line('views', '1131', 'purple_pay_factory_contract_address_qs[0].contract_abi',
                                          purple_pay_factory_contract_address_qs[0].contract_abi)
                print_statement_with_line('views', '1132', 'chain_id', chain_id)

                contract = create_contract_instance(purple_pay_factory_contract_address_qs[0].address,
                                                    purple_pay_factory_contract_address_qs[0].contract_abi, chain_id)

                purple_pay_multisig_address_qs = PurplePayMultisigContract.objects.filter(
                    blockchain_network=blockchain_network.id)

                print_statement_with_line('views', '1140', 'purple_pay_multisig_address_qs',
                                          purple_pay_multisig_address_qs)

                burner_contract_address = get_burner_contract_address(
                    contract, payment_id, currency_token_address, amount_in_current_currency_as_smallest_unit,
                    user_scw_final_address_to,
                    purple_pay_multisig_address_qs[0].address)  # ToDo - maintain a mapping of merchant SCW to network
                print_statement_with_line('views', '1146', 'burner_contract_address', burner_contract_address)

                # Generate QR Code String
                if currency.currency_type.name == 'Native':
                    qr_code_string = f'ethereum:{burner_contract_address}@{currency_chain_id}?value={amount_in_current_currency_as_smallest_unit}'
                    print(qr_code_string)
                else:
                    qr_code_string = f'ethereum:{currency_token_address}@{chain_id}/transfer?address={burner_contract_address}&uint256={amount_in_current_currency_as_smallest_unit}'
                    print(qr_code_string)

                data = {
                    "payment_id": payment_id,
                    "currency": currency.id,
                    "burner_address": burner_contract_address,
                    "order_amount": amount_in_current_currency,
                    "payment_status": PaymentStatus.objects.get(name="In Progress").id,
                    "is_used_for_payment": False,
                    "conversion_rate_in_usd": exchange_rate_current_currency_per_usd,
                    "qr_code_string": qr_code_string
                }

                burner_address_serializer = self.get_serializer_class('payment_burner_address')(data=data)
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
            response['data']['description'] = description

            response['message'] = CREATE_BURNER_ADDRESS_SUCCESS
            # logger.info(response)
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response['message'] = CREATE_BURNER_ADDRESS_FAIL
            response['error'] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class PaymentBurnerAddressVerifyDetail4(generics.GenericAPIView):
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
        response = dict(data=dict(), message="", error="")
        try:
            if payment_id is None:
                response['data'] = {}
                response['message'] = PAYMENT_ID_MISSING_FAIL
                return Response(response, status=status.HTTP_200_OK)

            payment_burner_address_qs = PaymentBurnerAddress.objects.filter(payment_id=payment_id)
            print(f'line 838 :: payment_burner_address_qs :: {payment_burner_address_qs}')

            if len(payment_burner_address_qs) == 0:
                response['data'] = {}
                response['message'] = BURNER_ADDRESS_UNAVAILABLE_AGAINST_PAYMENT_ID_FAIL
                return Response(response, status=status.HTTP_200_OK)

            payment_status_in_progress = PaymentStatus.objects.get(name=PAYMENT_STATUS_IN_PROGRESS)
            payment_status_completed = PaymentStatus.objects.get(name=PAYMENT_STATUS_COMPLETED)

            payment_burner_obj = PaymentBurner.objects.get(id=payment_id)
            blockchain_network = payment_burner_obj.blockchain_network
            # print_statement_with_line('views', '849', 'payment_burner_obj', payment_burner_obj)

            payment_completed_in_burner_address_flag = False
            payment_burner_address_true_qs = PaymentBurnerAddress.objects.filter(payment_id=payment_id).filter(
                is_used_for_payment=True)
            print("LINE 1915::", "payment_burner_address_true_qs::", payment_burner_address_true_qs)

            ####### First call - payment not made to any address yet
            if len(payment_burner_address_true_qs) == 0:  # No payment made yet
                # payment_burner_address_qs = PaymentBurnerAddress.objects.filter(payment_id=payment_id)
                for payment_burner_address_obj in payment_burner_address_qs:
                    burner_address = payment_burner_address_obj.burner_address
                    token_instance = payment_burner_address_obj.currency
                    token_type = token_instance.currency_type.name.lower()
                    token_address = token_instance.token_address_on_network

                    print("LINE 1926", "::token_instance::", token_instance)

                    # fetch balance of given address
                    if token_instance.currency_type.name.lower() == 'native':
                        amount_in_burner_address = get_burner_address_balance_native(burner_address,
                                                                                     blockchain_network.chain_id)
                    else:
                        amount_in_burner_address = get_burner_address_balance(burner_address, token_instance,
                                                                              erc20_token_abi,
                                                                              blockchain_network.chain_id)
                    # print("LINE 1931")
                    # print("#" * 200)
                    # print("#" * 200)
                    # print("payment_burner_address_obj.order_amount::", payment_burner_address_obj.order_amount)
                    # print("in 10^decimals", payment_burner_address_obj.order_amount * (
                    #         10 ** token_instance.decimals))
                    # print("amount_in_burner_address::", amount_in_burner_address)
                    # print("#" * 200)
                    # print("#" * 200)
                    if payment_burner_address_obj.order_amount * (
                            10 ** token_instance.decimals) <= amount_in_burner_address:
                        payment_completed_in_burner_address_flag = True

                        print("The specific payment_burner_address of burner_address table")
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
                                burner_address, blockchain_network.chain_id)
                            print("LINE 1955")
                        else:
                            burner_address_transaction_details = get_transaction_details_using_block_explorer_erc20(
                                burner_address, token_address, blockchain_network.chain_id)
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
                            payment_instance=payment_burner_data_for_response_copy,
                            chain_id=blockchain_network.chain_id
                        )
                        # print_statement_with_line('views', 1524, 'kwarg_dict', kwarg_dict)

                        if payment_burner_address_obj.burner_contract_deploy_status == DEPLOY_STATUS_NOT_DEPLOY:
                            start_thread_to_deploy_and_disburse(deploy_and_disburse, kwarg_dict)

                        if payment_burner_address_obj.burner_contract_deploy_status == DEPLOY_STATUS_FAILURE_DEPLOY:
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
                            token['conversion_rate'] = element.conversion_rate_in_usd
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
                        response['message'] = PAYMENT_COMPLETED_SUCCESS
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
                        token['conversion_rate'] = element.conversion_rate_in_usd
                        token["transfer_to_merchant_transaction_hash"] = element.transfer_to_merchant_transaction_hash
                        token["burner_contract_deploy_status"] = element.burner_contract_deploy_status
                        token["burner_contract_deploy_failure_reason"] = element.burner_contract_deploy_failure_reason
                        tokens_for_response.append(token)

                    response['data']['id'] = payment_id
                    response['data']['payment_details'] = {}
                    response['data']['tokens'] = tokens_for_response
                    response['payment_status'] = payment_status_in_progress.name
                    response['message'] = payment_status_in_progress.name
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
                            burner_address, blockchain_network.chain_id)
                    else:
                        burner_address_transaction_details = get_transaction_details_using_block_explorer_erc20(
                            burner_address, token_address, blockchain_network.chain_id)
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
                    payment_instance=payment_burner_data_for_response_copy,
                    chain_id=blockchain_network.chain_id
                )
                # print_statement_with_line('views', 1524, 'kwarg_dict',
                #                           kwarg_dict)
                # print_statement_with_line('views', 1543,
                #                           'payment_burner_address_true_obj.burner_contract_deploy_status',
                #                           payment_burner_address_true_obj.burner_contract_deploy_status)
                if (payment_burner_address_true_obj.burner_contract_deploy_status == DEPLOY_STATUS_NOT_DEPLOY
                        or payment_burner_address_true_obj.burner_contract_deploy_status == DEPLOY_STATUS_FAILURE_DEPLOY):
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
                    token['conversion_rate'] = element.conversion_rate_in_usd
                    token["transfer_to_merchant_transaction_hash"] = element.transfer_to_merchant_transaction_hash
                    token["burner_contract_deploy_status"] = element.burner_contract_deploy_status
                    token["burner_contract_deploy_failure_reason"] = element.burner_contract_deploy_failure_reason
                    tokens_for_response.append(token)

                response['data']['id'] = payment_id
                response['data']['payment_details'] = payment_burner_data_for_response
                response['data']['tokens'] = tokens_for_response
                response['payment_status'] = payment_status_completed.name
                response['message'] = payment_status_completed.name
                return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            print(e)
            response['data']['id'] = payment_id
            response['data']['payment_details'] = {}
            response['data']['tokens'] = []
            response['payment_status'] = None
            response['message'] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


# Sample APIs
class PaymentBurnerAddressSampleGetCreateUpdate(generics.GenericAPIView):
    serializers = {
        'payment': PaymentBurnerSampleSerializer,
        'payment_burner_address': PaymentBurnerAddressSampleSerializer,
    }
    default_serializer_class = PaymentBurnerAddressSampleSerializer
    permission_classes = [AllowAny]

    def get_serializer_class(self, serializer_type):
        if serializer_type == 'payment':
            return self.serializers.get('payment')
        if serializer_type == 'payment_burner_address':
            return self.serializers.get('payment_burner_address')
        return self.default_serializer_class

    def post(self, request):
        response = dict(data={"tokens": []}, message="", error="")

        try:
            connected_wallet_address = request.data.get('connected_wallet_address', None)

            # Validate api_key and user_id
            # api_key_in_db = APIKey.objects.filter(id=api_key)
            # # print(f"api_key_in_db: ${api_key_in_db}")
            # if len(api_key_in_db) == 0:
            #     return Response("No such API Key found!", status=status.HTTP_200_OK)
            #
            payment_burner_sample_qs = PaymentBurnerSample.objects.filter(final_address_to=connected_wallet_address)
            if len(payment_burner_sample_qs) > 10:
                response['message'] = "You have exhausted your 10 trial transactions!"
                return Response(response, status=status.HTTP_200_OK)

            request.data['user'] = None
            request.data['final_address_to'] = connected_wallet_address
            request.data['currency'] = Currency.objects.get(
                symbol_primary=request.data.get('currency', 'usd').upper()).id

            payment_status_in_progress = PaymentStatus.objects.get(name=PAYMENT_STATUS_IN_PROGRESS)
            request.data['payment_status'] = payment_status_in_progress.id

            ## Add a filter depending on network requested from frontend - 137/Polygon Mainnet as default
            chain_id = str(request.data.get('chain_id', '5'))
            print_statement_with_line('views', '1208', 'chain_id', chain_id)
            blockchain_network = BlockchainNetwork.objects.get(chain_id=chain_id)
            # print('blockchain_network::::', blockchain_network)
            print_statement_with_line('views', '1069', 'blockchain_network', blockchain_network)
            request.data['blockchain_network'] = blockchain_network.id
            request.data['initial_block_number'] = get_latest_block_number(chain_id)
            print_statement_with_line('views', '1072', 'request_data', request.data)
            payment_serializer = self.get_serializer_class('payment')(data=request.data)
            if payment_serializer.is_valid():
                payment_serializer.save()

            payment_id = str(payment_serializer.data.get('id', None))
            description = str(payment_serializer.data.get('description', None))
            # print('560', payment_id)

            # All tokens

            # all currencies qs for requested network
            all_currencies_qs = Currency.objects.exclude(currency_type__name='Fiat').filter(
                blockchain_network=blockchain_network.id)

            print_statement_with_line('views', '1084', 'all_currencies_qs', all_currencies_qs)
            #
            # amount_in_that_token
            order_amount = payment_serializer.data.get('order_amount', None)  # in Dollar
            # 100 US Dollar
            # Which api
            exchange_rates = json.loads(requests.get(COINGECKO_EXCHANGE_RATE_1BTC_URL).text).get('rates', {})
            exchange_rate_usd_per_btc = exchange_rates.get('usd', None)

            # merchant final scw address
            # user_id_for_api_key_in_db = api_key_in_db[0].user.id
            # user_profile = UserProfile.objects.filter(user=user_id_for_api_key_in_db)
            user_scw_final_address_to = connected_wallet_address

            # purple_pay_multisig_address - defined above
            payment_status_in_progress = PaymentStatus.objects.get(name=PAYMENT_STATUS_IN_PROGRESS)
            payment_status_completed = PaymentStatus.objects.get(name=PAYMENT_STATUS_COMPLETED)

            purple_pay_factory_contract_address_qs = PurplePayFactoryContract.objects.filter(
                blockchain_network=blockchain_network.id)
            print_statement_with_line('views', '1105', 'purple_pay_factory_contract_address_qs',
                                      purple_pay_factory_contract_address_qs)
            if not purple_pay_factory_contract_address_qs:
                response['message'] = PURPLE_PAY_FACTORY_CONTRACT_UNAVAILABLE
                return Response(response, status=status.HTTP_200_OK)

            # Extract coingecko_id
            coingecko_ids = [element.coingecko_id for element in all_currencies_qs]
            coingecko_ids_string = ",".join(coingecko_ids)
            exchange_rates_vs_1usd_url = f"{COINGECKO_EXCHANGE_RATE_VS_1USD_URL}?ids={coingecko_ids_string}&vs_currencies=usd"
            exchange_rates_vs_1usd_res = json.loads(requests.get(exchange_rates_vs_1usd_url).text)
            for currency in all_currencies_qs:
                print_statement_with_line('views', '1110', 'currency',
                                          currency)
                currency_chain_id = currency.blockchain_network.chain_id
                # purple_pay_factory_contract_address_qs = PurplePayFactoryContract.objects.filter(
                #     blockchain_network=currency.blockchain_network.id)
                # if not purple_pay_factory_contract_address_qs:
                #     continue
                # print(f'purple_pay_factory_contract_address: {purple_pay_factory_contract_address_qs}')
                currency_network_name = currency.blockchain_network.name
                currency_token_address = currency.token_address_on_network

                # if currency.symbol_primary.lower() in ['usdc', 'usdt']:
                #     exchange_rate_current_currency_per_btc = exchange_rate_usd_per_btc
                # else:
                #     exchange_rate_current_currency_per_btc = exchange_rates.get(currency.coingecko_id)
                # if exchange_rate_current_currency_per_btc is None:
                #     continue
                exchange_rate_current_currency_per_usd = exchange_rates_vs_1usd_res.get(currency.coingecko_id,
                                                                                        {'usd': None}).get('usd', None)
                if exchange_rate_current_currency_per_usd is None:
                    continue
                amount_in_current_currency = order_amount / exchange_rate_current_currency_per_usd
                amount_in_current_currency_as_smallest_unit = int(
                    amount_in_current_currency * (10 ** currency.decimals))
                # print('603', amount_in_current_currency_as_smallest_unit)
                print_statement_with_line('views', '1130', 'purple_pay_factory_contract_address_qs[0].address',
                                          purple_pay_factory_contract_address_qs[0].address)
                print_statement_with_line('views', '1131', 'purple_pay_factory_contract_address_qs[0].contract_abi',
                                          purple_pay_factory_contract_address_qs[0].contract_abi)
                print_statement_with_line('views', '1132', 'chain_id', chain_id)

                contract = create_contract_instance(purple_pay_factory_contract_address_qs[0].address,
                                                    purple_pay_factory_contract_address_qs[0].contract_abi, chain_id)

                purple_pay_multisig_address_qs = PurplePayMultisigContract.objects.filter(
                    blockchain_network=blockchain_network.id)

                print_statement_with_line('views', '1140', 'purple_pay_multisig_address_qs',
                                          purple_pay_multisig_address_qs)

                burner_contract_address = get_burner_contract_address(
                    contract, payment_id, currency_token_address, amount_in_current_currency_as_smallest_unit,
                    user_scw_final_address_to,
                    purple_pay_multisig_address_qs[0].address)  # ToDo - maintain a mapping of merchant SCW to network
                print_statement_with_line('views', '1146', 'burner_contract_address', burner_contract_address)
                data = {
                    "payment_id": payment_id,
                    "currency": currency.id,
                    "burner_address": burner_contract_address,
                    "order_amount": amount_in_current_currency,
                    "payment_status": PaymentStatus.objects.get(name="In Progress").id,
                    "is_used_for_payment": False,
                }

                burner_address_serializer = self.get_serializer_class('payment_burner_address')(data=data)
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
            response['data']['description'] = description

            response['message'] = CREATE_BURNER_ADDRESS_SUCCESS
            # logger.info(response)
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response['message'] = CREATE_BURNER_ADDRESS_FAIL
            response['error'] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class PaymentBurnerAddressSampleVerifyDetail(generics.GenericAPIView):
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
        response = dict(data=dict(), message="", error="")
        try:
            if payment_id is None:
                response['data'] = {}
                response['message'] = PAYMENT_ID_MISSING_FAIL
                return Response(response, status=status.HTTP_200_OK)

            payment_burner_address_qs = PaymentBurnerAddress.objects.filter(payment_id=payment_id)
            print(f'line 838 :: payment_burner_address_qs :: {payment_burner_address_qs}')

            if len(payment_burner_address_qs) == 0:
                response['data'] = {}
                response['message'] = BURNER_ADDRESS_UNAVAILABLE_AGAINST_PAYMENT_ID_FAIL
                return Response(response, status=status.HTTP_200_OK)

            payment_status_in_progress = PaymentStatus.objects.get(name=PAYMENT_STATUS_IN_PROGRESS)
            payment_status_completed = PaymentStatus.objects.get(name=PAYMENT_STATUS_COMPLETED)

            payment_burner_obj = PaymentBurner.objects.get(id=payment_id)
            blockchain_network = payment_burner_obj.blockchain_network
            # print_statement_with_line('views', '849', 'payment_burner_obj', payment_burner_obj)

            payment_completed_in_burner_address_flag = False
            payment_burner_address_true_qs = PaymentBurnerAddress.objects.filter(payment_id=payment_id).filter(
                is_used_for_payment=True)
            print("LINE 1915::", "payment_burner_address_true_qs::", payment_burner_address_true_qs)

            ####### First call - payment not made to any address yet
            if len(payment_burner_address_true_qs) == 0:  # No payment made yet
                # payment_burner_address_qs = PaymentBurnerAddress.objects.filter(payment_id=payment_id)
                for payment_burner_address_obj in payment_burner_address_qs:
                    burner_address = payment_burner_address_obj.burner_address
                    token_instance = payment_burner_address_obj.currency
                    token_type = token_instance.currency_type.name.lower()
                    token_address = token_instance.token_address_on_network

                    print("LINE 1926", "::token_instance::", token_instance)

                    # fetch balance of given address
                    if token_instance.currency_type.name.lower() == 'native':
                        amount_in_burner_address = get_burner_address_balance_native(burner_address,
                                                                                     blockchain_network.chain_id)
                    else:
                        amount_in_burner_address = get_burner_address_balance(burner_address, token_instance,
                                                                              erc20_token_abi,
                                                                              blockchain_network.chain_id)
                    print("LINE 1931")
                    if payment_burner_address_obj.order_amount * (
                            10 ** token_instance.decimals) <= amount_in_burner_address:
                        payment_completed_in_burner_address_flag = True

                        print("The specific payment_burner_address of burner_address table")
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
                                burner_address, blockchain_network.chain_id)
                            print("LINE 1955")
                        else:
                            burner_address_transaction_details = get_transaction_details_using_block_explorer_erc20(
                                burner_address, token_address, blockchain_network.chain_id)
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
                            payment_instance=payment_burner_data_for_response_copy,
                            chain_id=blockchain_network.chain_id
                        )
                        # print_statement_with_line('views', 1524, 'kwarg_dict', kwarg_dict)

                        if payment_burner_address_obj.burner_contract_deploy_status == DEPLOY_STATUS_NOT_DEPLOY:
                            start_thread_to_deploy_and_disburse(deploy_and_disburse, kwarg_dict)

                        if payment_burner_address_obj.burner_contract_deploy_status == DEPLOY_STATUS_FAILURE_DEPLOY:
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
                        response['message'] = PAYMENT_COMPLETED_SUCCESS
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
                    response['message'] = payment_status_in_progress.name
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
                            burner_address, blockchain_network.chain_id)
                    else:
                        burner_address_transaction_details = get_transaction_details_using_block_explorer_erc20(
                            burner_address, token_address, blockchain_network.chain_id)
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
                    payment_instance=payment_burner_data_for_response_copy,
                    chain_id=blockchain_network.chain_id
                )
                # print_statement_with_line('views', 1524, 'kwarg_dict',
                #                           kwarg_dict)
                # print_statement_with_line('views', 1543,
                #                           'payment_burner_address_true_obj.burner_contract_deploy_status',
                #                           payment_burner_address_true_obj.burner_contract_deploy_status)
                if (payment_burner_address_true_obj.burner_contract_deploy_status == DEPLOY_STATUS_NOT_DEPLOY
                        or payment_burner_address_true_obj.burner_contract_deploy_status == DEPLOY_STATUS_FAILURE_DEPLOY):
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
                response['message'] = payment_status_completed.name
                return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            print(e)
            response['data']['id'] = payment_id
            response['data']['payment_details'] = {}
            response['data']['tokens'] = []
            response['payment_status'] = None
            response['message'] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
