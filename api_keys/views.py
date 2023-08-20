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
from commons.utils import generate_secret_for_api_key
from commons.app_codes import (ERROR_DETAILS, API_REQUEST_STATUS_DETAILS, SUCCESS, FAIL,
                               UNKNOWN_ERROR, INVALID_REQUEST, INVALID_REQUEST_BODY,
                               INVALID_SIGNATURE, INVALID_TIMESTAMP, INVALID_API_KEY,
                               MISSING_API_KEY, INVALID_NONCE, MISSING_NONCE, WRONG_HTTP_METHOD,
                               REQUIRED_PARAM_EMPTY_OR_BAD)


class APIKeyGetCreateUpdate(generics.GenericAPIView):
    serializer_class = APIKeySerializer
    permission_classes = [IsAuthenticated | IsAdminUser, ]

    def get(self, request):
        """
        # Description: retrieves list of all API Keys and associated information for a user
        # URL: <BASE_URL>/api_keys/
        # Method: GET

        # Query Parameters
        - No parameters

        # Permissions
        - User must be authenticated and have a valid token

        :param request: -
        :return: { "data": {
                        "asLlist": [{
                            "id": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "user": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "secretKey": "c39XXXXXXXXXXXXXXXXXXXXXXX3f9009",
                            "createdAt": "2023-08-12T10:57:07.810438Z",
                            "modifiedAt": "2023-08-12T10:57:07.810460Z",
                            "keyName": "APIKey1"
                            },
                            {
                            "id": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "user": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "secretKey": "c39XXXXXXXXXXXXXXXXXXXXXXX3f9009",
                            "createdAt": "2023-08-12T10:57:07.810438Z",
                            "modifiedAt": "2023-08-12T10:57:07.810460Z",
                            "keyName": "APIKey2"
                            },
                        ]},
                    "message": "Successfully retrieved api keys",
                    "status": "SUCCESS",
                    "code": "200000",
                    "error": ""
                }
        """
        response = dict(data=list(), message="", status="", code="", error="")

        try:
            user_id = self.request.user.id
            api_key_qs = APIKey.objects.filter(user=user_id)
            serializer = self.serializer_class(api_key_qs, many=True)
            db_data = serializer.data

            response_data = list()
            for element in db_data:
                data = dict()
                data['id'] = element.get('id', None)
                data["user"] = element.get("user", None)
                data["secret_key"] = element.get("secret_key", None)
                data["created_at"] = element.get("created_at", None)
                data["modified_at"] = element.get("modified_at", None)
                data["key_name"] = element.get("key_name", None)
                data["status"] = element.get("api_key_status", None)
                response_data.append(data)

            response['data'] = response_data
            response['message'] = GET_API_KEYS_SUCCESS
            response['status'] = SUCCESS
            response['code'] = API_REQUEST_STATUS_DETAILS[SUCCESS]['code']
            logger.info(response)
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response['message'] = "Unable to fetch api keys for the given user"
            response['status'] = FAIL
            response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][UNKNOWN_ERROR]["name"]
            response['error'] = str(e)    #API_REQUEST_STATUS_DETAILS[FAIL]['details'][UNKNOWN_ERROR]["message"]
            logger.info(response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        """
        # Description: creates a new apikey for a user
        # URL: <BASE_URL>/api_keys/
        # Method: POST

        # Query Parameters
        - No parameters

        # Permissions
        - User must be authenticated and have a valid token

        :param request: { "keyName": "user name for key"}
        :return: { "data": {
                        "apiKey": {
                            "id": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "user": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "secretKey": "c39XXXXXXXXXXXXXXXXXXXXXXX3f9009",
                            "createdAt": "2023-08-12T10:57:07.810438Z",
                            "modifiedAt": "2023-08-12T10:57:07.810460Z",
                            "keyName": "APIKey1"
                            }
                        },
                    "message": "Successfully created api key",
                    "status": "SUCCESS",
                    "code": "200000",
                    "error": ""
                }
        """

        response = dict(data=dict(), message="", status="", code="", error="")

        try:
            user_id = self.request.user.id

            request_data = dict()
            request_data['user'] = user_id
            request_data['key_name'] = self.request.data.get('key_name', None)
            request_data['api_key_status'] = self.request.data.get('status', None)    # ACTIVE, INACTIVE
            print(request_data)

            secret_key = generate_secret_for_api_key()

            serializer = self.serializer_class(data=request_data)

            # If: serializer is valid
            if serializer.is_valid():
                serializer.validated_data['secret_key'] = secret_key
                serializer.save()
                db_data = serializer.data
                response_data = dict()
                response_data['id'] = db_data.get('id', None)
                response_data['user'] = db_data.get('user', None)
                response_data['secret_key'] = db_data.get('secret_key', None)
                response_data['created_at'] = db_data.get('created_at', None)
                response_data['modified_at'] = db_data.get('modified_at', None)
                response_data['key_name'] = db_data.get('key_name', None)
                response_data['status'] = db_data.get('api_key_status', None)  # ACTIVE, INACTIVE

                # Prepare response
                response['data'] = response_data
                response['message'] = CREATE_APIKEY_SUCCESS
                response['status'] = SUCCESS
                response['code'] = API_REQUEST_STATUS_DETAILS[SUCCESS]['code']
                logger.info(response)
                return Response(response, status=status.HTTP_200_OK)

            # Else: serializer is invalid
            else:
                response['message'] = CREATE_APIKEY_FAIL
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["name"]
                logger.error(serializer.errors)
                print(serializer.errors)
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            response['message'] = CREATE_APIKEY_FAIL
            response['status'] = FAIL
            response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
            response['error'] = str(e)
            logger.error(response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        """
        # Description: updates a specific api key for a user

        # URL: <BASE_URL>/api_keys/
        # Method: PUT

        # Query Parameters
        - No parameters

        # Permissions
        - User must be authenticated and have a valid token

        :param request: {
                            "id": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "keyName": "APIKey1"
                            }
        :return: { "data": {
                        "apiKey": {
                            "id": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "user": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "secretKey": "c39XXXXXXXXXXXXXXXXXXXXXXX3f9009",
                            "createdAt": "2023-08-12T10:57:07.810438Z",
                            "modifiedAt": "2023-08-12T10:57:07.810460Z",
                            "keyName": "APIKey1"
                            }
                        },
                    "message": "Successfully updated api key",
                    "status": "SUCCESS",
                    "code": "200000",
                    "error": ""
                }
        """
        response = dict(data=dict(apiKey=dict()), message="", error="")

        try:
            user_id = self.request.user.id
            api_key = self.request.data.get('id', None)

            request_data = dict()
            print('request_data: ', request_data)
            if not api_key:
                response['message'] = "API Key is Missing"
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["name"]
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            api_key_qs = APIKey.objects.filter(user=user_id).filter(id=api_key)

            if len(api_key_qs) == 0:
                response['message'] = "API Key is Invalid"
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_API_KEY]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_API_KEY]["name"]
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            if 'key_name' in self.request.data:
                request_data['key_name'] = request.data.get('key_name', None)
            if 'status' in self.request.data:
                request_data['api_key_status'] = request.data.get('status', None)  # ACTIVE, INACTIVE
            request_data['user'] = user_id

            api_key_obj = api_key_qs[0]
            api_key_serializer = self.serializer_class(api_key_obj, data=request_data,
                                                       partial=True)
            if api_key_serializer.is_valid():
                api_key_serializer.save()
                response_data = dict()
                response_data['id'] = api_key_serializer.data.get('id', None)
                response_data['user'] = api_key_serializer.data.get('user', None)
                response_data['created_at'] = api_key_serializer.data.get('created_at', None)
                response_data['modified_at'] = api_key_serializer.data.get('modified_at', None)
                response_data['secret_key'] = api_key_serializer.data.get('secret_key', None)
                response_data['status'] = api_key_serializer.data.get('api_key_status', None)
                response_data['key_name'] = api_key_serializer.data.get('key_name', None)

                print(response_data)
                # Prepare response
                response['data'] = response_data
                response['message'] = "API Key updated successfully"
                response['status'] = SUCCESS
                response['code'] = API_REQUEST_STATUS_DETAILS[SUCCESS]['code']
                logger.info(response)
                return Response(response, status=status.HTTP_200_OK)
            else:
                errors = api_key_serializer.errors
                print(errors)
                response['message'] = "API Key could not be updated"
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["name"]
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            response['message'] = "API Key could not be updated"
            response['status'] = FAIL
            response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
            response['error'] = str(e)
            logger.error(response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class APIKeyDelete(generics.DestroyAPIView):
    serializer_class = APIKeySerializer
    permission_classes = [IsAuthenticated | IsAdminUser, ]

    def delete(self, request, *args, **kwargs):
        """
        # Description: deletes a specific api key for a user

        # URL: <BASE_URL>/api_keys/<id>
        # Method: DELETE

        # Query Parameters
        - api key id in URL path

        # Permissions
        - User must be authenticated and have a valid token

        :param request: -
        :return: { "data": {
                        "apiKey": {
                            "id": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51"}
                        },
                    "message": "Successfully deleted api key",
                    "status": "SUCCESS",
                    "code": "200000",
                    "error": ""
                }
        """
        response = dict(data=dict(), message="", error="")

        try:
            api_key = self.kwargs.get('api_key', None)
            print('KWARG:', self.kwargs)
            if not api_key:
                response['message'] = "API Key is missing in the path"
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST]["name"]
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            user_id = self.request.user.id
            api_key_qs = APIKey.objects.filter(user=user_id).filter(id=api_key)

            if len(api_key_qs) == 0:
                response['message'] = "API Key not found"
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_API_KEY]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_API_KEY]["name"]
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            if api_key_qs:
                api_key_obj = api_key_qs[0]
                api_key_obj.delete()

                response['data'] = {"id": api_key, "deleted": True}
                response['message'] = f'{api_key} has been deleted'
                response['status'] = SUCCESS
                response['code'] = API_REQUEST_STATUS_DETAILS[SUCCESS]['code']
                return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response['message'] = 'Could not delete the API Key'
            response['status'] = FAIL
            response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST]["code"]
            response['error'] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class APIKeyGetSCW(generics.GenericAPIView):
    serializer_class = APIKeySerializer
    permission_classes = [AllowAny, ]

    def get(self, request, api_key):
        """
        # Description: retrieves list of smart contract wallets associated to an api key
        # URL: <BASE_URL>/api_keys/sc_wallet/<id>
        # Method: GET

        # Query Parameters
        - No parameters

        # Permissions
        - User must be authenticated and have a valid token

        :param request: -
        :return: { "data": {
                        "smartContractWalletList": [{
                            "address": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            }]
                        },
                    "message": "Successfully retrieved smart contract wallets associated to an api key",
                    "status": "SUCCESS",
                    "code": "200000",
                    "error": ""
                }
        """
        response = dict(data=dict(), message="", status="", code="", error="")

        try:
            api_key_qs = APIKey.objects.filter(id=api_key)
            if not api_key_qs:
                response['message'] = API_KEY_INVALID
                logger.info(response)
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            api_key_obj = api_key_qs[0]
            user_profile_obj = UserProfile.objects.get(user=api_key_obj.user)
            if not user_profile_obj:
                response['message'] = USER_PROFILE_FAIL_NOT_FOUND
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST]["code"]
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            smart_contract_wallet_address = user_profile_obj.user_smart_contract_wallet_address

            response['data'] = {'smart_contract_wallet_address': smart_contract_wallet_address}
            response['message'] = "Successfully fetched smart contract addresses related to the user"
            response['status'] = SUCCESS
            response['code'] = API_REQUEST_STATUS_DETAILS[SUCCESS]['code']
            logger.info(response)
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response['message'] = EXCEPTION_OCCURRED
            response['status'] = FAIL
            response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST]["code"]
            response['error'] = str(e)
            logger.info(response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class APIKeyGetCreateUpdateV2(generics.GenericAPIView):
    serializer_class = APIKeySerializer
    permission_classes = [IsAuthenticated | IsAdminUser, ]

    def get(self, request):
        """
        # Description: retrieves list of all API Keys and associated information for a user
        # URL: <BASE_URL>/api_keys/
        # Method: GET

        # Query Parameters
        - No parameters

        # Permissions
        - User must be authenticated and have a valid token

        :param request: -
        :return: { "data": {
                        "list": [{
                            "id": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "user": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "secretKey": "c39XXXXXXXXXXXXXXXXXXXXXXX3f9009",
                            "createdAt": "2023-08-12T10:57:07.810438Z",
                            "modifiedAt": "2023-08-12T10:57:07.810460Z",
                            "keyName": "APIKey1"
                            },
                            {
                            "id": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "user": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "secretKey": "c39XXXXXXXXXXXXXXXXXXXXXXX3f9009",
                            "createdAt": "2023-08-12T10:57:07.810438Z",
                            "modifiedAt": "2023-08-12T10:57:07.810460Z",
                            "keyName": "APIKey2"
                            },
                        ]},
                    "message": "Successfully retrieved api keys",
                    "status": "SUCCESS",
                    "code": "200000",
                    "error": ""
                }
        """
        response = dict(data=dict(asList=list()), message="", status="", code="", error="")

        try:
            user_id = self.request.user.id
            api_key_qs = APIKey.objects.filter(user=user_id)
            serializer = self.serializer_class(api_key_qs, many=True)
            db_data = serializer.data

            response_data = list()
            for element in db_data:
                data = dict()
                data['id'] = element.get('id', None)
                data["user"] = element.get("user", None)
                data["secretKey"] = element.get("secret_key", None)
                data["createdAt"] = element.get("created_at", None)
                data["modifiedAt"] = element.get("modified_at", None)
                data["keyName"] = element.get("key_name", None)
                data['status'] = element.get('status', None)  # ACTIVE, INACTIVE
                response_data.append(data)

            response['data']['asList'] = response_data
            response['message'] = GET_API_KEYS_SUCCESS
            response['status'] = SUCCESS
            response['code'] = API_REQUEST_STATUS_DETAILS[SUCCESS]['code']
            logger.info(response)
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response['message'] = "Unable to fetch api keys for the given user"
            response['status'] = FAIL
            response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][UNKNOWN_ERROR]["name"]
            response['error'] = str(e)    #API_REQUEST_STATUS_DETAILS[FAIL]['details'][UNKNOWN_ERROR]["message"]
            logger.info(response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        """
        # Description: creates a new apikey for a user
        # URL: <BASE_URL>/api_keys/
        # Method: POST

        # Query Parameters
        - No parameters

        # Permissions
        - User must be authenticated and have a valid token

        :param request: { "keyName": "user name for key"}
        :return: { "data": {
                        "apiKey": {
                            "id": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "user": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "secretKey": "c39XXXXXXXXXXXXXXXXXXXXXXX3f9009",
                            "createdAt": "2023-08-12T10:57:07.810438Z",
                            "modifiedAt": "2023-08-12T10:57:07.810460Z",
                            "keyName": "APIKey1"
                            }
                        },
                    "message": "Successfully created api key",
                    "status": "SUCCESS",
                    "code": "200000",
                    "error": ""
                }
        """

        response = dict(data=dict(), message="", status="", code="", error="")

        try:
            user_id = self.request.user.id

            request_data = dict()
            request_data['user'] = user_id
            request_data['key_name'] = self.request.data.get('keyName', None)
            request_data['status'] = self.request.data.get('status', None)
            secret_key = generate_secret_for_api_key()

            serializer = self.serializer_class(data=request_data)

            # If: serializer is valid
            if serializer.is_valid():
                serializer.validated_data['secret_key'] = secret_key
                serializer.save()
                db_data = serializer.data
                response_data = dict()
                response_data['id'] = db_data.get('id', None)
                response_data['user'] = db_data.get('user', None)
                response_data['secretKey'] = db_data.get('secret_key', None)
                response_data['createdAt'] = db_data.get('created_at', None)
                response_data['modifiedAt'] = db_data.get('modified_at', None)
                response_data['keyName'] = db_data.get('key_name', None)
                response_data['status'] = db_data.get('status', None)
                # Prepare response
                response['data']['apiKey'] = response_data
                response['message'] = CREATE_APIKEY_SUCCESS
                response['status'] = SUCCESS
                response['code'] = API_REQUEST_STATUS_DETAILS[SUCCESS]['code']
                logger.info(response)
                return Response(response, status=status.HTTP_200_OK)

            # Else: serializer is invalid
            else:
                response['message'] = CREATE_APIKEY_FAIL
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["name"]
                logger.error(serializer.errors)
                print(serializer.errors)
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            response['message'] = CREATE_APIKEY_FAIL
            response['status'] = FAIL
            response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
            response['error'] = str(e)
            logger.error(response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        """
        # Description: updates a specific api key for a user

        # URL: <BASE_URL>/api_keys/
        # Method: PUT

        # Query Parameters
        - No parameters

        # Permissions
        - User must be authenticated and have a valid token

        :param request: {
                            "id": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "keyName": "APIKey1"
                            }
        :return: { "data": {
                        "apiKey": {
                            "id": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "user": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "secretKey": "c39XXXXXXXXXXXXXXXXXXXXXXX3f9009",
                            "createdAt": "2023-08-12T10:57:07.810438Z",
                            "modifiedAt": "2023-08-12T10:57:07.810460Z",
                            "keyName": "APIKey1"
                            }
                        },
                    "message": "Successfully updated api key",
                    "status": "SUCCESS",
                    "code": "200000",
                    "error": ""
                }
        """
        response = dict(data=dict(), message="", error="")

        try:
            user_id = self.request.user.id
            api_key = self.request.data.get('id', None)

            request_data = dict()
            print('request_data: ', request_data)
            if not api_key:
                response['message'] = "API Key is Missing"
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["name"]
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            api_key_qs = APIKey.objects.filter(user=user_id).filter(id=api_key)

            if len(api_key_qs) == 0:
                response['message'] = "API Key is Invalid"
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_API_KEY]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_API_KEY]["name"]
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            if 'keyName' in self.request.data:
                request_data['key_name'] = request.data.get('keyName', None)
            if 'status' in self.request.data:
                request_data['status'] = request.data.get('status', None)

            request_data['user'] = user_id

            api_key_obj = api_key_qs[0]
            api_key_serializer = self.serializer_class(api_key_obj, data=request_data,
                                                       partial=True)
            if api_key_serializer.is_valid():
                api_key_serializer.save()
                response_data = dict()
                response_data['id'] = api_key_serializer.data.get('id', None)
                response_data['user'] = api_key_serializer.data.get('user', None)
                response_data['createdAt'] = api_key_serializer.data.get('created_at', None)
                response_data['modifiedAt'] = api_key_serializer.data.get('modified_at', None)
                response_data['secretKey'] = api_key_serializer.data.get('secret_key', None)
                response_data['status'] = api_key_serializer.data.get('status', None)
                response_data['keyName'] = api_key_serializer.data.get('key_name', None)

                print(response_data)
                # Prepare response
                response['data']['apiKey'] = response_data
                response['message'] = "API Key updated successfully"
                response['status'] = SUCCESS
                response['code'] = API_REQUEST_STATUS_DETAILS[SUCCESS]['code']
                logger.info(response)
                return Response(response, status=status.HTTP_200_OK)
            else:
                errors = api_key_serializer.errors
                print(errors)
                response['message'] = "API Key could not be updated"
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["name"]
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            response['message'] = "API Key could not be updated"
            response['status'] = FAIL
            response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
            response['error'] = str(e)
            logger.error(response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class APIKeyDeleteV2(generics.DestroyAPIView):
    serializer_class = APIKeySerializer
    permission_classes = [IsAuthenticated | IsAdminUser, ]

    def delete(self, request, *args, **kwargs):
        """
        # Description: deletes a specific api key for a user

        # URL: <BASE_URL>/api_keys/<id>
        # Method: DELETE

        # Query Parameters
        - api key id in URL path

        # Permissions
        - User must be authenticated and have a valid token

        :param request: -
        :return: { "data": {
                        "apiKey": {
                            "id": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51"}
                        },
                    "message": "Successfully deleted api key",
                    "status": "SUCCESS",
                    "code": "200000",
                    "error": ""
                }
        """
        response = dict(data=dict(), message="", error="")

        try:
            api_key = self.kwargs.get('api_key', None)
            print('KWARG:', self.kwargs)
            if not api_key:
                response['message'] = "API Key is missing in the path"
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST]["name"]
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            user_id = self.request.user.id
            api_key_qs = APIKey.objects.filter(user=user_id).filter(id=api_key)

            if len(api_key_qs) == 0:
                response['message'] = "API Key not found"
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_API_KEY]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_API_KEY]["name"]
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            if api_key_qs:
                api_key_obj = api_key_qs[0]
                api_key_obj.delete()

                response['data'] = {"id": api_key}
                response['message'] = f'{api_key} has been deleted'
                response['status'] = SUCCESS
                response['code'] = API_REQUEST_STATUS_DETAILS[SUCCESS]['code']
                return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response['message'] = 'Could not delete the API Key'
            response['status'] = FAIL
            response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST]["code"]
            response['error'] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class APIKeyGetSCWV2(generics.GenericAPIView):
    serializer_class = APIKeySerializer
    permission_classes = [AllowAny, ]

    def get(self, request, api_key):
        """
        # Description: retrieves list of smart contract wallets associated to an api key
        # URL: <BASE_URL>/api_keys/sc_wallet/<id>
        # Method: GET

        # Query Parameters
        - No parameters

        # Permissions
        - User must be authenticated and have a valid token

        :param request: -
        :return: { "data": {
                        "asList": [{
                            "address": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            }]
                        },
                    "message": "Successfully retrieved smart contract wallets associated to an api key",
                    "status": "SUCCESS",
                    "code": "200000",
                    "error": ""
                }
        """
        response = dict(data=dict(asList=list()), message="", status="", code="", error="")

        try:
            api_key_qs = APIKey.objects.filter(id=api_key)
            if not api_key_qs:
                response['message'] = API_KEY_INVALID
                logger.info(response)
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            api_key_obj = api_key_qs[0]
            user_profile_obj = UserProfile.objects.get(user=api_key_obj.user)
            if not user_profile_obj:
                response['message'] = USER_PROFILE_FAIL_NOT_FOUND
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST]["code"]
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            smart_contract_wallet_address = user_profile_obj.user_smart_contract_wallet_address

            response['data']['asList'].append({'smartContractWalletAddress': smart_contract_wallet_address})
            response['message'] = USER_PROFILE_SUCCESS_FOUND
            response['status'] = SUCCESS
            response['code'] = API_REQUEST_STATUS_DETAILS[SUCCESS]['code']
            logger.info(response)
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response['message'] = EXCEPTION_OCCURRED
            response['status'] = FAIL
            response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST]["code"]
            response['error'] = str(e)
            logger.info(response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)




# class APIKeyGetSCW(generics.GenericAPIView):
#     serializer_class = APIKeySerializer
#     permission_classes = [AllowAny, ]
#
#     def get(self, request, api_key):
#         response = dict(data={}, message="", error="")
#         try:
#             api_key_obj = APIKey.objects.get(id=api_key)
#             if not api_key_obj:
#                 response['message'] = 'API Key Invalid'
#                 logger.info(response)
#                 return Response(response, status=status.HTTP_200_OK)
#             user_profile_obj = UserProfile.objects.get(user=api_key_obj.user)
#             if not user_profile_obj:
#                 response['message'] = 'User Profile not found'
#                 return Response(response, status=status.HTTP_200_OK)
#
#             smart_contract_wallet_address = user_profile_obj.user_smart_contract_wallet_address
#             response['data'] = {'smart_contract_wallet_address': smart_contract_wallet_address}
#             response['message'] = 'Success!'
#             logger.info(response)
#             return Response(response, status=status.HTTP_200_OK)
#         except Exception as e:
#             response['message'] = EXCEPTION_OCCURRED
#             response['error'] = str(e)
#             logger.info(response)
#             return Response(response, status=status.HTTP_400_BAD_REQUEST)
