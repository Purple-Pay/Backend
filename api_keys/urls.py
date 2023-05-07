from django.urls import path
# from .views import APIKeyListCreate, APIKeyRetrieveUpdateDelete
from .views import APIKeyGetCreateUpdate, APIKeyDelete, APIKeyGetSCW

urlpatterns = [
    path('', APIKeyGetCreateUpdate.as_view(), name='api_key_get_create_update'),
    path('<str:api_key>/', APIKeyDelete.as_view(), name='api_key_delete'),
    path('<str:api_key>/', APIKeyGetSCW.as_view(), name='api_key_get_scw')
]
