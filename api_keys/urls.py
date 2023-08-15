from django.urls import path
# from .views import APIKeyListCreate, APIKeyRetrieveUpdateDelete
from .views import (APIKeyGetCreateUpdate, APIKeyDelete, APIKeyGetSCW,
                    APIKeyGetCreateUpdateV2, APIKeyDeleteV2, APIKeyGetSCWV2)

urlpatterns = [
    path('', APIKeyGetCreateUpdate.as_view(), name='api_key_get_create_update'),
    path('delete/<str:api_key>', APIKeyDelete.as_view(), name='api_key_delete'),
    path('scw/<str:api_key>/', APIKeyGetSCW.as_view(), name='api_key_get_scw'),
    path('v2', APIKeyGetCreateUpdateV2.as_view(), name='api_key_get_create_update'),
    path('v2/delete/<str:api_key>', APIKeyDeleteV2.as_view(), name='api_key_delete'),
    path('v2/scw/<str:api_key>/', APIKeyGetSCWV2.as_view(), name='api_key_get_scw')
]
