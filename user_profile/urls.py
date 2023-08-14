from django.urls import path
from .views import (
    UserProfileGetCreateUpdateDelete,
    UserTypeListCreate,
    UserTypeRetrieveUpdateDelete,
    UserSmartContractWalletAddressGetCreateUpdateDelete, WebhookGetCreateUpdate,
    WebhookDelete, WebhookActivityGetCreateUpdate, UserProfileGetCreateUpdateDeleteV2,
    UserSmartContractWalletAddressGetCreateUpdateDeleteV2)

urlpatterns = [
    path('',
         UserProfileGetCreateUpdateDelete.as_view(), name='user_profile_get_create_update_delete'),
    path('user_type/', UserTypeListCreate.as_view(), name='user_type_list_create'),
    path('user_type/<str:id>', UserTypeRetrieveUpdateDelete.as_view(), name='user_type_get_update_delete'),
    path('user_scw/', UserSmartContractWalletAddressGetCreateUpdateDelete.as_view(),
         name='user_scw_get_create_update_delete'),
    path('webhook/delete/<str:webhookId>', WebhookDelete.as_view(),
         name='webhook_delete'),
    path('webhook/', WebhookGetCreateUpdate.as_view(),
         name='webhook_get_create_update'),
    path('webhook_activity/', WebhookActivityGetCreateUpdate.as_view(),
         name='webhook_activity_get_create_update'),
    path('v2',
         UserProfileGetCreateUpdateDeleteV2.as_view(), name='user_profile_get_create_update_delete'),
    path('v2/user_scw', UserSmartContractWalletAddressGetCreateUpdateDeleteV2.as_view(),
         name='user_scw_get_create_update_delete'),
]
