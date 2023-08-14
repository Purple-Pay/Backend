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
    WEBHOOK_URL_STATUS, WEBHOOK_EVENT_TYPE, USER_TYPES_DB_TO_API, USER_TYPES_API_TO_DB_REVERSE
)
from commons.utils import generate_secret_for_webhook
from commons.app_codes import (SUCCESS, FAIL, ERROR_DETAILS, UNKNOWN_ERROR, INVALID_REQUEST,
                               INVALID_REQUEST_BODY, INVALID_SIGNATURE, INVALID_TIMESTAMP, INVALID_API_KEY,
                               MISSING_API_KEY, INVALID_NONCE, MISSING_NONCE, WRONG_HTTP_METHOD,
                               REQUIRED_PARAM_EMPTY_OR_BAD, API_REQUEST_STATUS_DETAILS, API_STATUS_ENUM)


class UserProfileGetCreateUpdateDelete(generics.GenericAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        """
        # Description: retrieves list of all user profile and their details for a user.
        Currently, it holds a single profile for each user. It will be extended to multiple profiles in the next versions.

        # URL: <BASE_URL>/user_profile/
        # Method: GET

        # Query Parameters
        - No parameters

        # Permissions
        - User must be authenticated and have a valid token

        :param request: -
        :return: { "data": {
                        "userProfileList": [{
                            "id": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "user": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "createdAt": "2023-08-12T10:57:07.810438Z",
                            "modifiedAt": "2023-08-12T10:57:07.810460Z",
                            "profileImage": null,
                            "firstName": "Demo_FirstName",
                            "middleName": "",
                            "lastName": "Demo_LastName",
                            "location": "India",
                            "company": "PP_Demo",
                            "agreedTermsAndConditions": true,
                            "agreedPrivacyPolicy": true,
                            "userEOAWalletAddress": "0x107C189B0aa1C309bA65FD6fc22bE1AA513A459C",
                            "userSmartContractWalletAddress": "0xc1F78584D944616C18CeB1841B5f381961fA5dcE",
                            "companyUrl": null,
                            "userType": "2598cb27-c16e-4783-94da-ab27d70b9a51",
                            "defaultNetwork": "a3af6fde-c4da-4cdf-b2e4-bc9e89efc373",
                            "email": "arunanksharan+democmt@gmail.com"
                            }]
                        },
                    "message": "Successfully retrieved user profile",
                    "status": "SUCCESS",
                    "code": "200000",
                    "error": ""
                }
        """
        response = dict(data=dict(), message="", status="", code="", error="")

        try:
            user_id = self.request.user.id
            user_profile_qs = UserProfile.objects.filter(user=user_id)

            if not user_profile_qs:
                data = {'id': None}
                response['data'] = data
                response['message'] = 'User profile not created yet'
                response['status'] = SUCCESS
                response['code'] = API_REQUEST_STATUS_DETAILS[SUCCESS]['code']
                return Response(response, status=status.HTTP_200_OK)

            user_profile_obj = user_profile_qs[0]
            # user_type_name = USER_TYPES_DB_TO_API.get(user_profile_obj.user_type.name, None)
            user_type = None
            if user_profile_obj.user_type.id:
                user_type = str(user_profile_obj.user_type.id)
            default_network = None
            if user_profile_obj.default_network:
                default_network = str(user_profile_obj.default_network.id)

            user_obj = User.objects.get(id=user_id)
            user_profile_serializer = self.serializer_class(user_profile_qs, many=True)
            db_data = user_profile_serializer.data

            response_data = list()
            for element in db_data:
                data = dict()
                data['id'] = element.get('id', None)
                data["user"] = element.get("user", None)
                data["created_at"] = element.get("created_at", None)
                data["modified_at"] = element.get("modified_at", None)
                data["profile_image"] = element.get("profile_image", None)
                data["first_name"] = element.get("first_name", None)
                data["middle_name"] = element.get("middle_name", None)
                data["last_name"] = element.get("last_name", None)
                data["location"] = element.get("location", None)
                data["company"] = element.get("company", None)
                data["agreed_terms_and_conditions"] = element.get("agreed_terms_and_conditions", None)
                data["agreed_privacy_policy"] = element.get("agreed_privacy_policy", None)
                data["user_wallet_address"] = element.get("user_wallet_address", None)
                data["user_smart_contract_wallet_address"] = element.get("user_smart_contract_wallet_address", None)
                data["company_url"] = element.get("company_url", None)
                data["user_type"] = user_type
                data["default_network"] = default_network
                data['email'] = user_obj.email
                response_data.append(data)

            response['data'] = response_data[0]
            response['message'] = GET_PROFILE_SUCCESS
            response['status'] = SUCCESS
            response['code'] = API_REQUEST_STATUS_DETAILS[SUCCESS]['code']
            logger.info(response)
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response_data = list()
            data = {'id': None}
            response_data.append(data)

            response['data'] = response_data[0]
            response['message'] = API_REQUEST_STATUS_DETAILS[INVALID_REQUEST]['name']
            response['status'] = FAIL
            response['code'] = API_REQUEST_STATUS_DETAILS[INVALID_REQUEST]['code']
            response['error'] = str(e)
            logger.info(response)
            return Response(response, status=status.HTTP_200_OK)

    def post(self, request):
        """
        # Description: creates a new user profile and their details for a user.
        Currently, it holds a single profile for each user. It will be extended to multiple profiles in the next versions.

        # URL: <BASE_URL>/user_profile/
        # Method: POST

        # Query Parameters
        - No parameters

        # Permissions
        - User must be authenticated and have a valid token

        :param request: -
        :return: { "data": {
                        "userProfile": {
                            "id": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "user": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "createdAt": "2023-08-12T10:57:07.810438Z",
                            "modifiedAt": "2023-08-12T10:57:07.810460Z",
                            "profileImage": null,
                            "firstName": "Demo_FirstName",
                            "middleName": "",
                            "lastName": "Demo_LastName",
                            "location": "India",
                            "company": "PP_Demo",
                            "agreedTermsAndConditions": true,
                            "agreedPrivacyPolicy": true,
                            "userEOAWalletAddress": "0x107C189B0aa1C309bA65FD6fc22bE1AA513A459C",
                            "userSmartContractWalletAddress": "0xc1F78584D944616C18CeB1841B5f381961fA5dcE",
                            "companyUrl": null,
                            "userType": "2598cb27-c16e-4783-94da-ab27d70b9a51",
                            "defaultNetwork": "a3af6fde-c4da-4cdf-b2e4-bc9e89efc373",
                            "email": "arunanksharan+democmt@gmail.com"
                            }
                        },
                    "message": "Successfully created user profile",
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
            print(request_data)

            if not request.data['first_name'] or request.data['first_name'] is None:
                response["message"] = "First Name is missing"
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[INVALID_REQUEST]['code']
                response['error'] = API_REQUEST_STATUS_DETAILS[INVALID_REQUEST]['name']
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            if not request.data['last_name'] or request.data['last_name'] is None:
                response["message"] = "Last Name is missing"
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[INVALID_REQUEST]['code']
                response['error'] = API_REQUEST_STATUS_DETAILS[INVALID_REQUEST]['name']
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            if not request.data['location'] or request.data['location'] is None:
                response["message"] = "Location is missing"
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[INVALID_REQUEST]['code']
                response['error'] = API_REQUEST_STATUS_DETAILS[INVALID_REQUEST]['name']
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            if not request.data['company'] or request.data['company'] is None:
                response["message"] = "Company is missing"
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[INVALID_REQUEST]['code']
                response['error'] = API_REQUEST_STATUS_DETAILS[INVALID_REQUEST]['name']
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            if not request.data['default_network'] or request.data['default_network'] is None:
                response["message"] = "Default Network is missing"
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[INVALID_REQUEST]['code']
                response['error'] = API_REQUEST_STATUS_DETAILS[INVALID_REQUEST]['name']
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            default_network_chain_id = request.data.get('default_network', None)
            blockchain_qs = BlockchainNetwork.objects.filter(chain_id=default_network_chain_id)

            if not blockchain_qs:
                response["message"] = "Default Network is Invalid"
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[INVALID_REQUEST]['code']
                response['error'] = API_REQUEST_STATUS_DETAILS[INVALID_REQUEST]['name']
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            request_data['default_network'] = blockchain_qs[0].id

            request_user_type = request.data.get('user_type', None)    # MERCHANT, INDIVIDUAL, NA
            # if request_user_type not in USER_TYPES_API_TO_DB_REVERSE:
            #     request_user_type = 'NA'
            # request_user_type_db = USER_TYPES_API_TO_DB_REVERSE[request_user_type]
            # user_type_id = UserType.objects.filter(name=request_user_type_db)[0].id

            request_data['user_type'] = request_user_type    #user_type_id
            request_data["profile_image"] = request.data.get("profile_image", None)
            request_data["first_name"] = request.data.get("first_name", None)
            request_data["middle_name"] = request.data.get("middle_name", None)
            request_data["last_name"] = request.data.get("last_name", None)
            request_data["location"] = request.data.get("location", None)
            request_data["company"] = request.data.get("company", None)
            request_data["agreed_terms_and_conditions"] = request.data.get("agreed_terms_and_conditions", None)
            request_data["agreed_privacy_policy"] = request.data.get("agreed_privacy_policy", None)
            request_data["user_wallet_address"] = request.data.get("user_wallet_address", None)
            request_data["user_smart_contract_wallet_address"] = request.data.get("user_smart_contract_wallet_address", None)
            request_data["company_url"] = request.data.get("company_url", None)

            serializer = self.serializer_class(data=request_data)
            user_obj = User.objects.get(id=user_id)
            if serializer.is_valid():
                serializer.save()
                data = serializer.data

                response_data = data    #request.data
                # response_data["defaultNetwork"] = int(response_data["defaultNetwork"])
                # response_data['id'] = data.get('id', None)
                # response_data['createdAt'] = data.get('created_at', None)
                # response_data['modifiedAt'] = data.get('modified_at', None)
                # response_data['user'] = data.get('user', None)
                response_data['email'] = user_obj.email

                response['data'] = response_data
                response['message'] = GET_PROFILE_SUCCESS
                response['status'] = SUCCESS
                response['code'] = API_REQUEST_STATUS_DETAILS[SUCCESS]['code']
                logger.info(response)
                return Response(response, status=status.HTTP_200_OK)
            else:
                response['data'] = {'id': None}
                response['message'] = CREATE_PROFILE_FAIL
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["name"]
                logger.error(serializer.errors)
                print(serializer.errors)
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            response['data'] = {'id': None}
            response['message'] = CREATE_PROFILE_FAIL
            response['status'] = FAIL
            response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
            response['error'] = str(e)
            logger.error(response['error'])
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        """
        # Description: updates a user profile and their details for a user.
        Currently, it holds a single profile for each user. It will be extended to multiple profiles in the next versions.

        # URL: <BASE_URL>/user_profile/
        # Method: PUT

        # Query Parameters
        - No parameters

        # Permissions
        - User must be authenticated and have a valid token

        :param request: - {
                            "id": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "profileImage": null,
                            "firstName": "Demo_FirstName",
                            "middleName": "",
                            "lastName": "Demo_LastName",
                            "location": "India",
                            "company": "PP_Demo",
                            "companyUrl": null,
                            "defaultNetwork": 137,
                            }
        :return: { "data": {
                        "userProfile": {
                            "id": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "user": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "createdAt": "2023-08-12T10:57:07.810438Z",
                            "modifiedAt": "2023-08-12T10:57:07.810460Z",
                            "profileImage": null,
                            "firstName": "Demo_FirstName",
                            "middleName": "",
                            "lastName": "Demo_LastName",
                            "location": "India",
                            "company": "PP_Demo",
                            "agreedTermsAndConditions": true,
                            "agreedPrivacyPolicy": true,
                            "userEOAWalletAddress": "0x107C189B0aa1C309bA65FD6fc22bE1AA513A459C",
                            "userSmartContractWalletAddress": "0xc1F78584D944616C18CeB1841B5f381961fA5dcE",
                            "companyUrl": null,
                            "userType": "MERCHANT",
                            "defaultNetwork": 137,
                            }
                        },
                    "message": "Successfully created user profile",
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
            print(request_data)
            user_profile_id = self.request.data.get('id', None)
            if not user_profile_id:
                response['message'] = "User Profile Id is missing"
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["name"]
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            user_profile_qs = UserProfile.objects.filter(user=user_id).filter(id=user_profile_id)
            if len(user_profile_qs) == 0:
                response['message'] = "User Profile Id is invalid"
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["name"]
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            default_network_chain_id = request.data['default_network']
            # blockchain_qs = BlockchainNetwork.objects.filter(chain_id=default_network_chain_id)

            # if not blockchain_qs:
            #     response["message"] = "Default Network is Invalid"
            #     response['status'] = FAIL
            #     response['code'] = API_REQUEST_STATUS_DETAILS[INVALID_REQUEST]['code']
            #     response['error'] = API_REQUEST_STATUS_DETAILS[INVALID_REQUEST]['name']
            #     return Response(response, status=status.HTTP_400_BAD_REQUEST)
            request_data['default_network'] = default_network_chain_id    #blockchain_qs[0].id

            # if 'userType' in request.data:
            #     request_user_type = request.data.get('userType', 'NA')    # MERCHANT, INDIVIDUAL, NA
            #     if request_user_type not in USER_TYPES_API_TO_DB_REVERSE:
            #         request_user_type = 'NA'
            #     request_user_type_db = USER_TYPES_API_TO_DB_REVERSE[request_user_type]
            #     user_type_id = UserType.objects.filter(name=request_user_type_db)[0].id
            #
            #     request_data['user_type'] = user_type_id

            if "profile_image" in request.data:
                request_data["profile_image"] = request.data.get("profile_image", None)
            if "first_name" in request.data:
                request_data["first_name"] = request.data.get("first_name", None)
            if "middle_name" in request.data:
                request_data["middle_name"] = request.data.get("middle_name", None)
            if "last_name" in request.data:
                request_data["last_name"] = request.data.get("last_name", None)
            if "location" in request.data:
                request_data["location"] = request.data.get("location", None)
            if "company" in request.data:
                request_data["company"] = request.data.get("company", None)
            # if "agreedTermsAndConditions" in request.data:
            #     request_data["agreed_terms_and_conditions"] = request.data.get("agreedTermsAndConditions", None)
            # if "agreedPrivacyPolicy" in request.data:
            #     request_data["agreed_privacy_policy"] = request.data.get("agreedPrivacyPolicy", None)
            # if "userEOAWalletAddress" in request.data:
            #     request_data["user_wallet_address"] = request.data.get("userEOAWalletAddress", None)
            # if "userSmartContractWalletAddress" in request.data:
            #     request_data["user_smart_contract_wallet_address"] = request.data.get("userSmartContractWalletAddress", None)
            if "company_url" in request.data:
                request_data["company_url"] = request.data.get("company_url", None)

            user_profile_obj = user_profile_qs[0]
            serializer = self.serializer_class(user_profile_obj, data=request_data,
                                                       partial=True)
            if serializer.is_valid():
                serializer.save()
                data = serializer.data
                response_data = request.data
                # response_data["default_network"] = int(response_data["defaultNetwork"])
                # response_data['modifiedAt'] = data.get('modified_at', None)

                response['data'] = response_data
                response['message'] = "Successfully updated user profile"
                response['status'] = SUCCESS
                response['code'] = API_REQUEST_STATUS_DETAILS[SUCCESS]['code']
                logger.info(response)
                return Response(response, status=status.HTTP_200_OK)
            else:
                response['message'] = "Failed to update profile"
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["name"]
                logger.error(serializer.errors)
                print(serializer.errors)
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            response['data'] = {}
            response['message'] = CREATE_PROFILE_FAIL
            response['status'] = FAIL
            response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
            response['error'] = str(e)
            logger.error(response['error'])
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """
        # Description: deletes a specific user profile for a user. It will be implemented soon.

        # URL: <BASE_URL>/user_profile/delete/<id>
        # Method: DELETE

        # Query Parameters
        - user profile id in URL path

        # Permissions
        - User must be authenticated and have a valid token

        :param request: -
        :return: { "data": {
                        "userProfile": {
                            "id": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51"}
                        },
                    "message": "Successfully deleted user profile",
                    "status": "SUCCESS",
                    "code": "200000",
                    "error": ""
                }
        """
        response = dict(data=dict(), message="", error="")

        try:
            # user_id = self.request.user.id
            # profile_obj = UserProfile.objects.get(user=user_id)
            # profile_obj.delete()
            # response['message'] = DELETE_PROFILE_SUCCESS
            # logger.info(response)
            response["message"] = "User Profile deletion feature will be enabled soon"
            response['status'] = SUCCESS
            response['code'] = API_REQUEST_STATUS_DETAILS[SUCCESS]['code']
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response['message'] = "User Profile deletion feature will be enabled soon"
            response['error'] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class UserProfileGetCreateUpdateDeleteV2(generics.GenericAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        """
        # Description: retrieves list of all user profile and their details for a user.
        Currently, it holds a single profile for each user. It will be extended to multiple profiles in the next versions.

        # URL: <BASE_URL>/user_profile/
        # Method: GET

        # Query Parameters
        - No parameters

        # Permissions
        - User must be authenticated and have a valid token

        :param request: -
        :return: { "data": {
                        "userProfileList": [{
                            "id": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "user": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "createdAt": "2023-08-12T10:57:07.810438Z",
                            "modifiedAt": "2023-08-12T10:57:07.810460Z",
                            "profileImage": null,
                            "firstName": "Demo_FirstName",
                            "middleName": "",
                            "lastName": "Demo_LastName",
                            "location": "India",
                            "company": "PP_Demo",
                            "agreedTermsAndConditions": true,
                            "agreedPrivacyPolicy": true,
                            "userEOAWalletAddress": "0x107C189B0aa1C309bA65FD6fc22bE1AA513A459C",
                            "userSmartContractWalletAddress": "0xc1F78584D944616C18CeB1841B5f381961fA5dcE",
                            "companyUrl": null,
                            "userType": "2598cb27-c16e-4783-94da-ab27d70b9a51",
                            "defaultNetwork": "a3af6fde-c4da-4cdf-b2e4-bc9e89efc373",
                            "email": "arunanksharan+democmt@gmail.com"
                            }]
                        },
                    "message": "Successfully retrieved user profile",
                    "status": "SUCCESS",
                    "code": "200000",
                    "error": ""
                }
        """
        response = dict(data=dict(apiKeyList=list()), message="", status="", code="", error="")

        try:
            user_id = self.request.user.id
            user_profile_qs = UserProfile.objects.filter(user=user_id)

            if not user_profile_qs:
                data = {'id': None}
                response['data']['userProfileList'].append(data)
                response['message'] = 'User profile not created yet'
                response['status'] = SUCCESS
                response['code'] = API_REQUEST_STATUS_DETAILS[SUCCESS]['code']
                return Response(response, status=status.HTTP_200_OK)

            user_profile_obj = user_profile_qs[0]
            user_type = USER_TYPES_DB_TO_API.get(user_profile_obj.user_type.name, None)
            default_network = None
            if user_profile_obj.default_network:
                default_network = user_profile_obj.default_network.chain_id

            user_obj = User.objects.get(id=user_id)
            user_profile_serializer = self.serializer_class(user_profile_qs, many=True)
            db_data = user_profile_serializer.data

            response_data = list()
            for element in db_data:
                data = dict()
                data['id'] = element.get('id', None)
                data["user"] = element.get("user", None)
                data["createdAt"] = element.get("created_at", None)
                data["modifiedAt"] = element.get("modified_at", None)
                data["profileImage"] = element.get("profile_image", None)
                data["firstName"] = element.get("first_name", None)
                data["middleName"] = element.get("middle_name", None)
                data["lastName"] = element.get("last_name", None)
                data["location"] = element.get("location", None)
                data["company"] = element.get("company", None)
                data["agreedTermsAndConditions"] = element.get("agreed_terms_and_conditions", None)
                data["agreedPrivacyPolicy"] = element.get("agreed_privacy_policy", None)
                data["userEOAWalletAddress"] = element.get("user_wallet_address", None)
                data["userSmartContractWalletAddress"] = element.get("user_smart_contract_wallet_address", None)
                data["companyUrl"] = element.get("company_url", None)
                data["userType"] = user_type
                data["defaultNetwork"] = default_network
                data['email'] = user_obj.email
                response_data.append(data)

            response['data']['userProfileList'] = response_data
            response['message'] = GET_PROFILE_SUCCESS
            response['status'] = SUCCESS
            response['code'] = API_REQUEST_STATUS_DETAILS[SUCCESS]['code']
            logger.info(response)
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response_data = list()
            data = {'id': None}
            response_data.append(data)

            response['data']['userProfileList'] = response_data
            response['message'] = API_REQUEST_STATUS_DETAILS[INVALID_REQUEST]['name']
            response['status'] = FAIL
            response['code'] = API_REQUEST_STATUS_DETAILS[INVALID_REQUEST]['code']
            response['error'] = str(e)
            logger.info(response)
            return Response(response, status=status.HTTP_200_OK)

    def post(self, request):
        """
        # Description: creates a new user profile and their details for a user.
        Currently, it holds a single profile for each user. It will be extended to multiple profiles in the next versions.

        # URL: <BASE_URL>/user_profile/
        # Method: POST

        # Query Parameters
        - No parameters

        # Permissions
        - User must be authenticated and have a valid token

        :param request: -
        :return: { "data": {
                        "userProfile": {
                            "id": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "user": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "createdAt": "2023-08-12T10:57:07.810438Z",
                            "modifiedAt": "2023-08-12T10:57:07.810460Z",
                            "profileImage": null,
                            "firstName": "Demo_FirstName",
                            "middleName": "",
                            "lastName": "Demo_LastName",
                            "location": "India",
                            "company": "PP_Demo",
                            "agreedTermsAndConditions": true,
                            "agreedPrivacyPolicy": true,
                            "userEOAWalletAddress": "0x107C189B0aa1C309bA65FD6fc22bE1AA513A459C",
                            "userSmartContractWalletAddress": "0xc1F78584D944616C18CeB1841B5f381961fA5dcE",
                            "companyUrl": null,
                            "userType": "2598cb27-c16e-4783-94da-ab27d70b9a51",
                            "defaultNetwork": "a3af6fde-c4da-4cdf-b2e4-bc9e89efc373",
                            "email": "arunanksharan+democmt@gmail.com"
                            }
                        },
                    "message": "Successfully created user profile",
                    "status": "SUCCESS",
                    "code": "200000",
                    "error": ""
                }
        """
        response = dict(data=dict(userProfile=dict()), message="", status="", code="", error="")
        try:
            user_id = self.request.user.id
            request_data = dict()
            request_data['user'] = user_id
            print(request_data)

            if not request.data['firstName'] or request.data['firstName'] is None:
                response["message"] = "First Name is missing"
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[INVALID_REQUEST]['code']
                response['error'] = API_REQUEST_STATUS_DETAILS[INVALID_REQUEST]['name']
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            if not request.data['lastName'] or request.data['lastName'] is None:
                response["message"] = "Last Name is missing"
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[INVALID_REQUEST]['code']
                response['error'] = API_REQUEST_STATUS_DETAILS[INVALID_REQUEST]['name']
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            if not request.data['location'] or request.data['location'] is None:
                response["message"] = "Location is missing"
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[INVALID_REQUEST]['code']
                response['error'] = API_REQUEST_STATUS_DETAILS[INVALID_REQUEST]['name']
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            if not request.data['company'] or request.data['company'] is None:
                response["message"] = "Company is missing"
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[INVALID_REQUEST]['code']
                response['error'] = API_REQUEST_STATUS_DETAILS[INVALID_REQUEST]['name']
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            if not request.data['defaultNetwork'] or request.data['defaultNetwork'] is None:
                response["message"] = "Default Network is missing"
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[INVALID_REQUEST]['code']
                response['error'] = API_REQUEST_STATUS_DETAILS[INVALID_REQUEST]['name']
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            default_network_chain_id = request.data['defaultNetwork']
            blockchain_qs = BlockchainNetwork.objects.filter(chain_id=default_network_chain_id)

            if not blockchain_qs:
                response["message"] = "Default Network is Invalid"
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[INVALID_REQUEST]['code']
                response['error'] = API_REQUEST_STATUS_DETAILS[INVALID_REQUEST]['name']
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            request_data['default_network'] = blockchain_qs[0].id

            request_user_type = request.data.get('userType', 'NA')    # MERCHANT, INDIVIDUAL, NA
            if request_user_type not in USER_TYPES_API_TO_DB_REVERSE:
                request_user_type = 'NA'
            request_user_type_db = USER_TYPES_API_TO_DB_REVERSE[request_user_type]
            user_type_id = UserType.objects.filter(name=request_user_type_db)[0].id

            request_data['user_type'] = user_type_id
            request_data["profile_image"] = request.data.get("profileImage", None)
            request_data["first_name"] = request.data.get("firstName", None)
            request_data["middle_name"] = request.data.get("middleName", None)
            request_data["last_name"] = request.data.get("lastName", None)
            request_data["location"] = request.data.get("location", None)
            request_data["company"] = request.data.get("company", None)
            request_data["agreed_terms_and_conditions"] = request.data.get("agreedTermsAndConditions", None)
            request_data["agreed_privacy_policy"] = request.data.get("agreedPrivacyPolicy", None)
            request_data["user_wallet_address"] = request.data.get("userEOAWalletAddress", None)
            request_data["user_smart_contract_wallet_address"] = request.data.get("userSmartContractWalletAddress", None)
            request_data["company_url"] = request.data.get("companyUrl", None)

            serializer = self.serializer_class(data=request_data)
            user_obj = User.objects.get(id=user_id)
            if serializer.is_valid():
                serializer.save()
                data = serializer.data

                response_data = request.data
                response_data["defaultNetwork"] = int(response_data["defaultNetwork"])
                response_data['id'] = data.get('id', None)
                response_data['createdAt'] = data.get('created_at', None)
                response_data['modifiedAt'] = data.get('modified_at', None)
                response_data['user'] = data.get('user', None)
                response_data['email'] = user_obj.email

                response['data']['userProfile'] = response_data
                response['message'] = GET_PROFILE_SUCCESS
                response['status'] = SUCCESS
                response['code'] = API_REQUEST_STATUS_DETAILS[SUCCESS]['code']
                logger.info(response)
                return Response(response, status=status.HTTP_200_OK)
            else:
                response['message'] = CREATE_PROFILE_FAIL
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["name"]
                logger.error(serializer.errors)
                print(serializer.errors)
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            response['data']['userProfile'] = {'id': None}
            response['message'] = CREATE_PROFILE_FAIL
            response['status'] = FAIL
            response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
            response['error'] = str(e)
            logger.error(response['error'])
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        """
        # Description: updates a user profile and their details for a user.
        Currently, it holds a single profile for each user. It will be extended to multiple profiles in the next versions.

        # URL: <BASE_URL>/user_profile/
        # Method: PUT

        # Query Parameters
        - No parameters

        # Permissions
        - User must be authenticated and have a valid token

        :param request: - {
                            "id": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "profileImage": null,
                            "firstName": "Demo_FirstName",
                            "middleName": "",
                            "lastName": "Demo_LastName",
                            "location": "India",
                            "company": "PP_Demo",
                            "companyUrl": null,
                            "defaultNetwork": 137,
                            }
        :return: { "data": {
                        "userProfile": {
                            "id": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "user": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "createdAt": "2023-08-12T10:57:07.810438Z",
                            "modifiedAt": "2023-08-12T10:57:07.810460Z",
                            "profileImage": null,
                            "firstName": "Demo_FirstName",
                            "middleName": "",
                            "lastName": "Demo_LastName",
                            "location": "India",
                            "company": "PP_Demo",
                            "agreedTermsAndConditions": true,
                            "agreedPrivacyPolicy": true,
                            "userEOAWalletAddress": "0x107C189B0aa1C309bA65FD6fc22bE1AA513A459C",
                            "userSmartContractWalletAddress": "0xc1F78584D944616C18CeB1841B5f381961fA5dcE",
                            "companyUrl": null,
                            "userType": "MERCHANT",
                            "defaultNetwork": 137,
                            }
                        },
                    "message": "Successfully created user profile",
                    "status": "SUCCESS",
                    "code": "200000",
                    "error": ""
                }
        """
        response = dict(data=dict(userProfile=dict()), message="", status="", code="", error="")

        try:
            user_id = self.request.user.id
            request_data = dict()
            request_data['user'] = user_id
            print(request_data)
            user_profile_id = self.request.data.get('id', None)
            if not user_profile_id:
                response['message'] = "User Profile Id is missing"
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["name"]
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            user_profile_qs = UserProfile.objects.filter(user=user_id).filter(id=user_profile_id)
            if len(user_profile_qs) == 0:
                response['message'] = "User Profile Id is invalid"
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["name"]
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            default_network_chain_id = request.data['defaultNetwork']
            blockchain_qs = BlockchainNetwork.objects.filter(chain_id=default_network_chain_id)

            if not blockchain_qs:
                response["message"] = "Default Network is Invalid"
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[INVALID_REQUEST]['code']
                response['error'] = API_REQUEST_STATUS_DETAILS[INVALID_REQUEST]['name']
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            request_data['default_network'] = blockchain_qs[0].id

            # if 'userType' in request.data:
            #     request_user_type = request.data.get('userType', 'NA')    # MERCHANT, INDIVIDUAL, NA
            #     if request_user_type not in USER_TYPES_API_TO_DB_REVERSE:
            #         request_user_type = 'NA'
            #     request_user_type_db = USER_TYPES_API_TO_DB_REVERSE[request_user_type]
            #     user_type_id = UserType.objects.filter(name=request_user_type_db)[0].id
            #
            #     request_data['user_type'] = user_type_id

            if "profileImage" in request.data:
                request_data["profile_image"] = request.data.get("profileImage", None)
            if "firstName" in request.data:
                request_data["first_name"] = request.data.get("firstName", None)
            if "middleName" in request.data:
                request_data["middle_name"] = request.data.get("middleName", None)
            if "lastName" in request.data:
                request_data["last_name"] = request.data.get("lastName", None)
            if "location" in request.data:
                request_data["location"] = request.data.get("location", None)
            if "company" in request.data:
                request_data["company"] = request.data.get("company", None)
            # if "agreedTermsAndConditions" in request.data:
            #     request_data["agreed_terms_and_conditions"] = request.data.get("agreedTermsAndConditions", None)
            # if "agreedPrivacyPolicy" in request.data:
            #     request_data["agreed_privacy_policy"] = request.data.get("agreedPrivacyPolicy", None)
            # if "userEOAWalletAddress" in request.data:
            #     request_data["user_wallet_address"] = request.data.get("userEOAWalletAddress", None)
            # if "userSmartContractWalletAddress" in request.data:
            #     request_data["user_smart_contract_wallet_address"] = request.data.get("userSmartContractWalletAddress", None)
            if "companyUrl" in request.data:
                request_data["company_url"] = request.data.get("companyUrl", None)

            user_profile_obj = user_profile_qs[0]
            serializer = self.serializer_class(user_profile_obj, data=request_data,
                                                       partial=True)
            if serializer.is_valid():
                serializer.save()
                data = serializer.data
                response_data = request.data
                response_data["defaultNetwork"] = int(response_data["defaultNetwork"])
                response_data['modifiedAt'] = data.get('modified_at', None)

                response['data']['userProfile'] = response_data
                response['message'] = "Successfully updated user profile"
                response['status'] = SUCCESS
                response['code'] = API_REQUEST_STATUS_DETAILS[SUCCESS]['code']
                logger.info(response)
                return Response(response, status=status.HTTP_200_OK)
            else:
                response['message'] = "Failed to update profile"
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["name"]
                logger.error(serializer.errors)
                print(serializer.errors)
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            response['data']['userProfile'] = request.data
            response['message'] = CREATE_PROFILE_FAIL
            response['status'] = FAIL
            response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
            response['error'] = str(e)
            logger.error(response['error'])
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """
        # Description: deletes a specific user profile for a user. It will be implemented soon.

        # URL: <BASE_URL>/user_profile/delete/<id>
        # Method: DELETE

        # Query Parameters
        - user profile id in URL path

        # Permissions
        - User must be authenticated and have a valid token

        :param request: -
        :return: { "data": {
                        "userProfile": {
                            "id": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51"}
                        },
                    "message": "Successfully deleted user profile",
                    "status": "SUCCESS",
                    "code": "200000",
                    "error": ""
                }
        """
        response = dict(data=dict(), message="", error="")

        try:
            # user_id = self.request.user.id
            # profile_obj = UserProfile.objects.get(user=user_id)
            # profile_obj.delete()
            # response['message'] = DELETE_PROFILE_SUCCESS
            # logger.info(response)
            response["message"] = "User Profile deletion feature will be enabled soon"
            response['status'] = SUCCESS
            response['code'] = API_REQUEST_STATUS_DETAILS[SUCCESS]['code']
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response['message'] = "User Profile deletion feature will be enabled soon"
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
        """
        # Description: retrieves list of all smart contract addresses for a user.
        Currently, it holds a single smart contract address for each user.
        It will be extended to multiple smart contract addresses in the next versions.

        # URL: <BASE_URL>/user_profile/
        # Method: GET

        # Query Parameters
        - No parameters

        # Permissions
        - User must be authenticated and have a valid token

        :param request: -
        :return: { "data": {
                        "walletAddressList": [{
                            "id": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "user": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "createdAt": "2023-08-12T10:57:07.810438Z",
                            "modifiedAt": "2023-08-12T10:57:07.810460Z",
                            "userEOAWalletAddress": "0x107C189B0aa1C309bA65FD6fc22bE1AA513A459C",
                            "userSmartContractWalletAddress": "0xc1F78584D944616C18CeB1841B5f381961fA5dcE",
                            }]
                        },
                    "message": "Successfully retrieved wallet addresses for the given user",
                    "status": "SUCCESS",
                    "code": "200000",
                    "error": ""
                }
        """
        response = dict(data=dict(), message="", status="", code="", error="")
        try:
            user_id = self.request.user.id
            queryset = UserSmartContractWalletAddress.objects.filter(user=user_id)
            serializer = self.serializer_class(queryset, many=True)

            response_data = list()

            for element in serializer.data:
                data = dict()
                data["id"] = element.get("id", None)
                data["user"] = element.get("user", None)
                data["created_at"] = element.get("created_at", None)
                data["modified_at"] = element.get("modified_at", None)
                data["user_wallet_address"] = element.get("user_wallet_address", None)
                data["user_smart_contract_wallet_address"] = element.get("user_smart_contract_wallet_address", None)

                blockchain_network = element.get('blockchain_network', None)
                chain_id = None
                if blockchain_network:
                    blockchain_network_qs = BlockchainNetwork.objects.filter(id=blockchain_network)
                    if blockchain_network_qs:
                        chain_id = int(blockchain_network_qs[0].chain_id)
                data['chain_id'] = chain_id
                response_data.append(data)

            response['data'] = response_data[0]
            response['message'] = "Wallet Addresses successfully fetched for the user"
            response['status'] = SUCCESS
            response['code'] = API_REQUEST_STATUS_DETAILS[SUCCESS]['code']
            logger.info(response)
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response['message'] = "Could not fetch wallet addresses for the given user"
            response['status'] = FAIL
            response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][UNKNOWN_ERROR]["name"]
            response['error'] = str(e)  # API_REQUEST_STATUS_DETAILS[FAIL]['details'][UNKNOWN_ERROR]["message"]
            logger.info(response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        """
        # Description: creates a new EOA and Smart Contract Wallet Address for a given user

        # URL: <BASE_URL>/user_profile/user_scw
        # Method: POST

        # Query Parameters
        -

        # Permissions
        - User must be authenticated and have a valid token
        :param request:
        {
            "chainId": "137",
            "userEOAWalletAddress": "0x107C189B0aa1C309bA65FD6fc22bE1AA513A459C",
            "userSmartContractWalletAddress": "0xc1F78584D944616C18CeB1841B5f381961fA5dcE",
        }
        :return: { "data": {
                        "walletAddress": {
                            'id': "303v58e2-1388-411c-a3f9-2662de0716d1",
                            'user': "30b658e2-1388-a3f9-411c-266d2e0716d1",
                            'createdAt': "2023-08-10T14:24:15.782737Z",
                            'modifiedAt': "2023-08-10T14:24:15.782737Z",
                            'chainId': "137",
                            'userEOAWalletAddress': "0x107C189B0aa1C309bA65FD6fc22bE1AA513A459C",
                            'userSmartContractWalletAddress': "0xc1F78584D944616C18CeB1841B5f381961fA5dcE",
                            }
                        },
                    "message": "Successfully created wallet address",
                    "status": "SUCCESS",
                    "code": "200000",
                    "error": ""
                    }
        """
        response = dict(data=dict(), message="", status="", code="", error="")

        try:
            request_data = dict()
            user_id = self.request.user.id
            request_data['user'] = user_id

            chain_id = request.data.get('chain_id', None)
            if not chain_id:
                response['message'] = 'Chain id is missing'
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["name"]
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            blockchain_network_qs = BlockchainNetwork.objects.filter(chain_id=chain_id)
            if not blockchain_network_qs:
                response['message'] = 'No such chain_id or blockchain network found'
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["name"]
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            request_data['blockchain_network'] = blockchain_network_qs[0].id

            user_wallet_address = request.data.get('user_wallet_address', None)
            if not user_wallet_address:
                response['message'] = 'User wallet address is missing'
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["name"]
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            user_sc_wallet_address = request.data.get('user_smart_contract_wallet_address', None)
            if not user_sc_wallet_address:
                response['message'] = 'User Smart Contract Wallet Address is missing'
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["name"]
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            request_data['user_wallet_address'] = user_wallet_address
            request_data['user_smart_contract_wallet_address'] = user_sc_wallet_address

            serializer = self.serializer_class(data=request_data)

            if serializer.is_valid():
                serializer.save()
                response_data = dict()
                response_data['id'] = serializer.data.get('id', None)
                response_data['user'] = serializer.data.get('user', None)
                response_data['created_at'] = serializer.data.get('created_at', None)
                response_data['modified_at'] = serializer.data.get('modified_at', None)
                response_data['chain_id'] = request.data.get('chain_id', None)
                response_data['user_wallet_address'] = serializer.data.get('user_wallet_address', None)
                response_data['user_smart_contract_wallet_address'] = serializer.data.get('user_smart_contract_wallet_address', None)

                response['data'] = response_data
                response['message'] = CREATE_USER_SMART_CONTRACT_WALLET_SUCCESS
                response['status'] = SUCCESS
                response['code'] = API_REQUEST_STATUS_DETAILS[SUCCESS]['code']
                logger.info(response)
                return Response(response, status=status.HTTP_200_OK)

            else:
                errors = serializer.errors
                response['message'] = CREATE_USER_SMART_CONTRACT_WALLET_FAIL
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["name"]
                logger.error(errors)
                print(errors)
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            response['message'] = CREATE_USER_SMART_CONTRACT_WALLET_FAIL
            response['status'] = FAIL
            response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
            response['error'] = str(e)
            logger.error(response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        """
        # Description: Update method will be enabled soon.
        It updates a new EOA and Smart Contract Wallet Address for a given user

        # URL: <BASE_URL>/user_profile/user_scw/<scw_id>
        # Method: POST

        # Query Parameters
        -

        # Permissions
        - User must be authenticated and have a valid token
        :param request:
        {
            "id": "303v58e2-1388-411c-a3f9-2662de0716d1",
            "chainId": "137",
            "userEOAWalletAddress": "0x107C189B0aa1C309bA65FD6fc22bE1AA513A459C",
            "userSmartContractWalletAddress": "0xc1F78584D944616C18CeB1841B5f381961fA5dcE",
        }
        :return: { "data": {
                        "walletAddress": {
                            'id': "303v58e2-1388-411c-a3f9-2662de0716d1",
                            'user': "30b658e2-1388-a3f9-411c-266d2e0716d1",
                            'createdAt': "2023-08-10T14:24:15.782737Z",
                            'modifiedAt': "2023-08-10T14:24:15.782737Z",
                            'chainId': "137",
                            'userEOAWalletAddress': "0x107C189B0aa1C309bA65FD6fc22bE1AA513A459C",
                            'userSmartContractWalletAddress': "0xc1F78584D944616C18CeB1841B5f381961fA5dcE",
                            }
                        },
                    "message": "Successfully updated wallet address",
                    "status": "SUCCESS",
                    "code": "200000",
                    "error": ""
                    }
        """

        response = dict(data=dict(), message="Update will be enabled soon", code="", status="", error="")
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
        """
        # Description: Delete method will be enabled soon
        :param request:
        :return:
        """
        response = dict(data=dict(), message="Delete will be enabled soon", error="")
        # user_id = self.request.user.id
        # profile_obj = UserProfile.objects.get(user=user_id)
        # profile_obj.delete()
        # response['message'] = DELETE_PROFILE_SUCCESS
        # logger.info(response)
        return Response(response, status=status.HTTP_400_BAD_REQUEST)


class UserSmartContractWalletAddressGetCreateUpdateDeleteV2(generics.GenericAPIView):
    serializer_class = UserSmartContractWalletAddressSerializer
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        """
        # Description: retrieves list of all smart contract addresses for a user.
        Currently, it holds a single smart contract address for each user.
        It will be extended to multiple smart contract addresses in the next versions.

        # URL: <BASE_URL>/user_profile/
        # Method: GET

        # Query Parameters
        - No parameters

        # Permissions
        - User must be authenticated and have a valid token

        :param request: -
        :return: { "data": {
                        "walletAddressList": [{
                            "id": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "user": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51",
                            "createdAt": "2023-08-12T10:57:07.810438Z",
                            "modifiedAt": "2023-08-12T10:57:07.810460Z",
                            "userEOAWalletAddress": "0x107C189B0aa1C309bA65FD6fc22bE1AA513A459C",
                            "userSmartContractWalletAddress": "0xc1F78584D944616C18CeB1841B5f381961fA5dcE",
                            }]
                        },
                    "message": "Successfully retrieved wallet addresses for the given user",
                    "status": "SUCCESS",
                    "code": "200000",
                    "error": ""
                }
        """
        response = dict(data=list(), message="", status="", code="", error="")
        try:
            user_id = self.request.user.id
            queryset = UserSmartContractWalletAddress.objects.filter(user=user_id)
            serializer = self.serializer_class(queryset, many=True)

            response_data = list()

            for element in serializer.data:
                data = dict()
                data["id"] = element.get("id", None)
                data["user"] = element.get("user", None)
                data["created_at"] = element.get("created_at", None)
                data["modified_at"] = element.get("modified_at", None)
                data["user_wallet_address"] = element.get("user_wallet_address", None)
                data["user_smart_contract_wallet_address"] = element.get("user_smart_contract_wallet_address", None)

                blockchain_network = element.get('blockchain_network', None)
                chain_id = None
                if blockchain_network:
                    blockchain_network_qs = BlockchainNetwork.objects.filter(id=blockchain_network)
                    if blockchain_network_qs:
                        chain_id = int(blockchain_network_qs[0].chain_id)
                data['chainId'] = chain_id
                response_data.append(data)

            response['data']['wallet_details'] = response_data
            response['data']['user'] = user_id
            response['message'] = "Wallet Addresses successfully fetched for the user"
            response['status'] = SUCCESS
            response['code'] = API_REQUEST_STATUS_DETAILS[SUCCESS]['code']
            logger.info(response)
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response['message'] = "Could not fetch wallet addresses for the given user"
            response['status'] = FAIL
            response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][UNKNOWN_ERROR]["name"]
            response['error'] = str(e)  # API_REQUEST_STATUS_DETAILS[FAIL]['details'][UNKNOWN_ERROR]["message"]
            logger.info(response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        """
        # Description: creates a new EOA and Smart Contract Wallet Address for a given user

        # URL: <BASE_URL>/user_profile/user_scw
        # Method: POST

        # Query Parameters
        -

        # Permissions
        - User must be authenticated and have a valid token
        :param request:
        {
            "chainId": "137",
            "userEOAWalletAddress": "0x107C189B0aa1C309bA65FD6fc22bE1AA513A459C",
            "userSmartContractWalletAddress": "0xc1F78584D944616C18CeB1841B5f381961fA5dcE",
        }
        :return: { "data": {
                        "walletAddress": {
                            'id': "303v58e2-1388-411c-a3f9-2662de0716d1",
                            'user': "30b658e2-1388-a3f9-411c-266d2e0716d1",
                            'createdAt': "2023-08-10T14:24:15.782737Z",
                            'modifiedAt': "2023-08-10T14:24:15.782737Z",
                            'chainId': "137",
                            'userEOAWalletAddress': "0x107C189B0aa1C309bA65FD6fc22bE1AA513A459C",
                            'userSmartContractWalletAddress': "0xc1F78584D944616C18CeB1841B5f381961fA5dcE",
                            }
                        },
                    "message": "Successfully created wallet address",
                    "status": "SUCCESS",
                    "code": "200000",
                    "error": ""
                    }
        """
        response = dict(data=dict(walletAddress=dict()), message="", status="", code="", error="")

        try:
            request_data = dict()
            print(self.request.data)
            user_id = self.request.user.id
            request_data['user'] = user_id

            chain_id = request.data.get('chainId', None)
            if not chain_id:
                response['message'] = 'Chain id is missing'
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["name"]
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            blockchain_network_qs = BlockchainNetwork.objects.filter(chain_id=chain_id)
            if not blockchain_network_qs:
                response['message'] = 'No such chain_id or blockchain network found'
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["name"]
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            request_data['blockchain_network'] = blockchain_network_qs[0].id

            user_wallet_address = request.data.get('user_wallet_address', None)
            if not user_wallet_address:
                response['message'] = 'User wallet address is missing'
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["name"]
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            user_sc_wallet_address = request.data.get('user_smart_contract_wallet_address', None)
            if not user_sc_wallet_address:
                response['message'] = 'User Smart Contract Wallet Address is missing'
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["name"]
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            request_data['user_wallet_address'] = user_wallet_address
            request_data['user_smart_contract_wallet_address'] = user_sc_wallet_address

            serializer = self.serializer_class(data=request.data)

            if serializer.is_valid():
                serializer.save()
                response_data = dict()
                response_data['id'] = serializer.data.get('id', None)
                response_data['user'] = serializer.data.get('user', None)
                response_data['created_at'] = serializer.data.get('created_at', None)
                response_data['modified_at'] = serializer.data.get('modified_at', None)
                response_data['chain_id'] = request.data.get('chainId', None)
                response_data['user_wallet_address'] = serializer.data.get('user_wallet_address', None)
                response_data['user_smart_contract_wallet_address'] = serializer.data.get('user_smart_contract_wallet_address', None)

                response['data']['wallet_details'] = response_data
                response['data']['user'] = user_id
                response['message'] = CREATE_USER_SMART_CONTRACT_WALLET_SUCCESS
                response['status'] = SUCCESS
                response['code'] = API_REQUEST_STATUS_DETAILS[SUCCESS]['code']
                logger.info(response)
                return Response(response, status=status.HTTP_200_OK)

            else:
                errors = serializer.errors
                response['message'] = CREATE_USER_SMART_CONTRACT_WALLET_FAIL
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["name"]
                logger.error(errors)
                print(errors)
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            response['message'] = CREATE_USER_SMART_CONTRACT_WALLET_FAIL
            response['status'] = FAIL
            response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
            response['error'] = str(e)
            logger.error(response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        """
        # Description: Update method will be enabled soon.
        It updates a new EOA and Smart Contract Wallet Address for a given user

        # URL: <BASE_URL>/user_profile/user_scw/<scw_id>
        # Method: POST

        # Query Parameters
        -

        # Permissions
        - User must be authenticated and have a valid token
        :param request:
        {
            "id": "303v58e2-1388-411c-a3f9-2662de0716d1",
            "chainId": "137",
            "userEOAWalletAddress": "0x107C189B0aa1C309bA65FD6fc22bE1AA513A459C",
            "userSmartContractWalletAddress": "0xc1F78584D944616C18CeB1841B5f381961fA5dcE",
        }
        :return: { "data": {
                        "walletAddress": {
                            'id': "303v58e2-1388-411c-a3f9-2662de0716d1",
                            'user': "30b658e2-1388-a3f9-411c-266d2e0716d1",
                            'createdAt': "2023-08-10T14:24:15.782737Z",
                            'modifiedAt': "2023-08-10T14:24:15.782737Z",
                            'chainId': "137",
                            'userEOAWalletAddress': "0x107C189B0aa1C309bA65FD6fc22bE1AA513A459C",
                            'userSmartContractWalletAddress': "0xc1F78584D944616C18CeB1841B5f381961fA5dcE",
                            }
                        },
                    "message": "Successfully updated wallet address",
                    "status": "SUCCESS",
                    "code": "200000",
                    "error": ""
                    }
        """

        response = dict(data=dict(), message="Update will be enabled soon", code="", status="", error="")
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
        """
        # Description: Delete method will be enabled soon
        :param request:
        :return:
        """
        response = dict(data=dict(), message="Delete will be enabled soon", error="")
        # user_id = self.request.user.id
        # profile_obj = UserProfile.objects.get(user=user_id)
        # profile_obj.delete()
        # response['message'] = DELETE_PROFILE_SUCCESS
        # logger.info(response)
        return Response(response, status=status.HTTP_400_BAD_REQUEST)


class WebhookGetCreateUpdate(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WebhookSerializer

    def get(self, request):
        """
        # Description: fetches list of all webhooks for a given user

        # URL: <BASE_URL>/webhook/
        # Method: GET

        # Query Parameters
        -

        # Permissions
        - User must be authenticated and have a valid token

        :param request: -
        :return: { "data": {
                        "webhookList": [{
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
                            }]
                        },
                    "message": "Successfully fetched webhooks for the user",
                    "status": "SUCCESS",
                    "code": "200000",
                    "error": ""
                    }
        """
        response = dict(data=dict(webhookList=list()), message="", status="", code="", error="")

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
            response['status'] = SUCCESS
            response['code'] = API_REQUEST_STATUS_DETAILS[SUCCESS]['code']
            logger.info(response)
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            response['message'] = 'Unable to fetch webhooks for the given user'
            response['status'] = FAIL
            response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][UNKNOWN_ERROR]["name"]
            response['error'] = str(e)  # API_REQUEST_STATUS_DETAILS[FAIL]['details'][UNKNOWN_ERROR]["message"]
            logger.info(response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        """
        # Description: creates a new webhook for a given user

        # URL: <BASE_URL>/webhook/
        # Method: POST

        # Query Parameters
        -

        # Permissions
        - User must be authenticated and have a valid token
        :param request:
        {
            'url': "https://<WEBHOOK_URL>",
            'status': "ACTIVE",
            'eventType': "SUCCESS",
            'description': "This is a sample request for creating webhooks for a given user id",
            'metadata': ""
        }
        :return: { "data": {
                        "webhook": {
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
                        },
                    "message": "Successfully created webhook",
                    "status": "SUCCESS",
                    "code": "200000",
                    "error": ""
                    }
        """
        response = dict(data=dict(webhook=dict()), message="", status="", code="", error="")
        request_data = dict()
        print(self.request.data)

        try:
            user_id = self.request.user.id

            request_data['event_type'] = request.data.get('eventType', None)
            if request_data['event_type'] and request_data['event_type'] not in WEBHOOK_EVENT_TYPE:
                response["message"] = "Webhook event type is invalid!"
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["name"]
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            if request_data['event_type'] == 'SUCCESS':
                webhook_qs_success = Webhook.objects.filter(event_type='SUCCESS')
                if len(webhook_qs_success) >= 2:
                    response["message"] = "You have crossed the limit for webhooks for a successful payment!"
                    response['status'] = FAIL
                    response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
                    response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["name"]
                    return Response(response, status=status.HTTP_400_BAD_REQUEST)
            elif request_data['event_type'] == 'FAIL':
                webhook_qs_fail = Webhook.objects.filter(event_type='FAIL')
                if len(webhook_qs_fail) >= 2:
                    response["message"] = "You have crossed the limit for webhooks for a failed payment!"
                    response['status'] = FAIL
                    response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
                    response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["name"]
                    return Response(response, status=status.HTTP_400_BAD_REQUEST)

            request_data['status'] = request.data.get('status', None)
            if request_data['status'] and request_data['status'] not in WEBHOOK_URL_STATUS:
                response["error"] = "Webhook status is invalid!"
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["name"]
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
                response['status'] = SUCCESS
                response['code'] = API_REQUEST_STATUS_DETAILS[SUCCESS]['code']
                logger.info(response)
                return Response(response, status=status.HTTP_200_OK)

            else:
                errors = webhook_serializer.errors
                response['message'] = "Webhook creation has failed"
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["name"]
                logger.error(errors)
                print(errors)
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            response['message'] = "Webhook creation has failed"
            response['status'] = FAIL
            response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
            response['error'] = str(e)
            logger.error(response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        """
        # Description: updates a new webhook for a given user

        # URL: <BASE_URL>/webhook/
        # Method: PUT

        # Query Parameters
        -

        # Permissions
        - User must be authenticated and have a valid token
        :param request:
        {
            'url': "https://<WEBHOOK_URL>",
            'status': "ACTIVE",
            'eventType': "SUCCESS",
            'description': "This is a sample request for webhooks list for a given user id",
            'metadata': ""
        }
        :return: { "data": {
                        "webhook": {
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
                        },
                    "message": "Successfully created webhook",
                    "status": "SUCCESS",
                    "code": "200000",
                    "error": ""
                    }
        """
        response = dict(data=dict(webhook=dict()), message="", status="", code="", error="")

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
                response['status'] = SUCCESS
                response['code'] = API_REQUEST_STATUS_DETAILS[SUCCESS]['code']
                logger.info(response)
                return Response(response, status=status.HTTP_200_OK)
            else:
                errors = webhook_serializer.errors
                print(errors)
                response['data'] = self.request.data
                response['message'] = 'Failed to updated the given webhook'
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["name"]
                logger.error(errors)
                print(errors)
                response['error'] = errors
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            response['message'] = 'Failed to updated the given webhook'
            response['status'] = FAIL
            response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST_BODY]["code"]
            response['error'] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class WebhookDelete(generics.DestroyAPIView):

    def delete(self, request, *args, **kwargs):
        """
        # Description: deletes a specific webhook for a user

        # URL: <BASE_URL>/webhook/delete/<webhook_id>
        # Method: DELETE

        # Query Parameters
        - webhook id in URL path

        # Permissions
        - User must be authenticated and have a valid token

        :param request: -
        :return: { "data": {
                        "webhook": {
                            "id": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51"}
                        },
                    "message": "Successfully deleted webhook",
                    "status": "SUCCESS",
                    "code": "200000",
                    "error": ""
                }
        """
        response = dict(data=dict(webhook=dict()), message="", error="")

        try:
            webhook_id = self.kwargs.get('webhook_id', None)
            print('KWARG:', self.kwargs)
            if not webhook_id:
                response['message'] = 'Webhook id is missing or invalid'
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST]["name"]
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            user_id = self.request.user.id
            webhook_qs = Webhook.objects.filter(user=user_id).filter(id=webhook_id)
            if webhook_qs:
                webhook_obj = webhook_qs[0]
                webhook_obj.delete()

                response['data'] = {'webhookId': webhook_id}
                response['message'] = f'{webhook_id} has been deleted'
                response['status'] = SUCCESS
                response['code'] = API_REQUEST_STATUS_DETAILS[SUCCESS]['code']
                return Response(response, status=status.HTTP_200_OK)
            else:
                response['data'] = {}
                response['message'] = 'Webhook not found for the given id'
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST]["name"]
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            response['message'] = 'Could not delete the webhook id'
            response['status'] = FAIL
            response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST]["code"]
            response['error'] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class WebhookActivityGetCreateUpdate(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WebhookActivitySerializer

    def get(self, request, webhook_id):
        """
        # Description: fetches list of all webhooks activity for a given user

        # URL: <BASE_URL>/webhookActivity/<webhook_id>
        # Method: GET

        # Query Parameters
        -

        # Permissions
        - User must be authenticated and have a valid token

        :param request: -
        :return: { "data": {
                        "webhookActivityList": [{
                            'id': "303v58e2-1388-411c-a3f9-2662de0716d1",
                            'user': "30b658e2-1388-a3f9-411c-266d2e0716d1",
                            'createdAt': "2023-08-10T14:24:15.782737Z",
                            'modifiedAt': "2023-08-10T14:24:15.782737Z",
                            'latestInteractionType': "SUCCESS",
                            'deliveryResponseBody': "{"status": "Success", "data" : "Payment confirmation received"}",
                            'deliveryResponseStatusCode': "200",
                            'requestTimestampInUnixMs': "1678340394",
                            'requestNonce': "43CA2D78492",
                            'requestSignature': "FFHHDFHOEQ7328074009490214BF23984RFHIUY32894DH389HR",
                            'requestPayload': { "merchantOrderId": "mer123",
                                                "purplePayOrderId: "65d7a2a3-89f0-4d7c-a1c2-2e19a7f8b63a",
                                                "transactionStatus": "COMPLETED",
                                                "transactionHash": "0x9d1aa83ea1bca6a1e9d5e7b6528d1bf72e8d4f26b18942b4c329617750dcf5d1"
                                                },
                            'errorLog': "",
                            '': "",
                            }]
                        },
                    "message": "Successfully fetched webhooks for the user",
                    "status": "SUCCESS",
                    "code": "200000",
                    "error": ""
                    }
        """
        response = dict(data=dict(webhookList=list()), message="", status="", code="", error="")

        try:
            webhook_id = self.kwargs.get('webhook_id', None)
            print('KWARG:', self.kwargs)
            if not webhook_id:
                response['message'] = 'Webhook id is missing or invalid'
                response['status'] = FAIL
                response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST]["code"]
                response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST]["name"]
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            user_id = self.request.user.id
            webhook_activity_qs = WebhookActivity.objects.filter(user=user_id).filter(webhook=webhook_id)
            serializer = self.serializer_class(webhook_activity_qs, many=True)
            response_data = list()
            for element in serializer.data:
                data = dict()
                data['id'] = element.get('id', None)
                data['user'] = element.get('user', None)
                data['createdAt'] = element.get('created_at', None)
                data['modifiedAt'] = element.get('modified_at', None)
                data['latestInteractionType'] = element.get('latest_interaction_type', None)
                data['deliveryResponseBody'] = element.get('delivery_response_body', None)
                data['deliveryResponseStatusCode'] = element.get('delivery_response_status_code', None)
                data['requestTimestampInUnixMs'] = element.get('request_timestamp_in_unix_ms', None)
                data['requestNonce'] = element.get('request_nonce', None)
                data['requestSignature'] = element.get('request_signature', None)
                data['requestPayload'] = element.get('request_payload', None)

                response_data.append(data)
            print(response_data)
            response['data'] = {
                'webhookActivityList': response_data
            }
            response['message'] = "Successfully fetched webhook activity for the given user"
            response['status'] = SUCCESS
            response['code'] = API_REQUEST_STATUS_DETAILS[SUCCESS]['code']
            logger.info(response)
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            response['message'] = 'Unable to fetch webhooks activity for the given user'
            response['status'] = FAIL
            response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][UNKNOWN_ERROR]["name"]
            response['error'] = str(e)  # API_REQUEST_STATUS_DETAILS[FAIL]['details'][UNKNOWN_ERROR]["message"]
            logger.info(response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class WebhookActivityDelete(generics.DestroyAPIView):

    def delete(self, request, *args, **kwargs):
        """
        # Description: deletes a specific webhook activity for a user

        # URL: <BASE_URL>/webhook_activity/delete/<webhookActivityId>
        # Method: DELETE

        # Query Parameters
        - webhook id in URL path

        # Permissions
        - User must be authenticated and have a valid token

        :param request: -
        :return: { "data": {
                        "webhookActivity": {
                            "id": "9aXXXX8a-XXXX-XXXX-XXXX-711XXXXXXX51"}
                        },
                    "message": "Successfully deleted webhook activity",
                    "status": "SUCCESS",
                    "code": "200000",
                    "error": ""
                }
        """
        response = dict(data=dict(webhook=dict()), message="", error="")

        try:
            response['message'] = 'This functionality will be enabled soon'
            response['status'] = FAIL
            response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST]["code"]
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
            # webhook_activity_id = self.kwargs.get('webhook_activity_id', None)
            # print('KWARG:', self.kwargs)
            # if not webhook_activity_id:
            #     response['message'] = 'Webhook id is missing or invalid'
            #     response['status'] = FAIL
            #     response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST]["code"]
            #     response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST]["name"]
            #     return Response(response, status=status.HTTP_400_BAD_REQUEST)
            # user_id = self.request.user.id
            # webhook_activity_qs = WebhookActivity.objects.filter(webhook__user=user_id).filter(id=webhook_activity_id)
            # if webhook_activity_qs:
            #     webhook_activity_obj = webhook_activity_qs[0]
            #     webhook_activity_obj.delete()
            #
            #     response['data'] = {'webhookActivityId': webhook_activity_id}
            #     response['message'] = f'{webhook_activity_id} has been deleted'
            #     response['status'] = SUCCESS
            #     response['code'] = API_REQUEST_STATUS_DETAILS[SUCCESS]['code']
            #     return Response(response, status=status.HTTP_200_OK)
            # else:
            #     response['data'] = {}
            #     response['message'] = 'Webhook Activity not found for the given id'
            #     response['status'] = FAIL
            #     response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST]["code"]
            #     response['error'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST]["name"]
            #     return Response(response, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            response['message'] = 'This functionality will be enabled soon'
            # 'Could not delete the webhook activity id'
            response['status'] = FAIL
            response['code'] = API_REQUEST_STATUS_DETAILS[FAIL]['details'][INVALID_REQUEST]["code"]
            response['error'] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
