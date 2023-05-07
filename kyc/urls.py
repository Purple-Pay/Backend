from django.urls import path
from .views import KYCProfileGetCreateUpdateDelete, KYCProviderListCreate, \
    KYCProviderRetrieveUpdateDelete, KYCProviderClaimRequestListUpdate, KYCProfilePolygonIdGetCreateUpdateDelete, KYCProfileRequiredSchemaView

urlpatterns = [
    path('', KYCProfileGetCreateUpdateDelete.as_view(), name='kyc_get_create_update_delete'),
    path('kyc_provider/', KYCProviderListCreate.as_view(), name='kyc_provider_list_create'),
    path('kyc_provider/<str:id>', KYCProviderRetrieveUpdateDelete.as_view(), name='kyc_provider_get_update_delete'),
    path('claim_requests/', KYCProviderClaimRequestListUpdate.as_view(), name='kyc_provider_claim_request_list_update'),
    path('polygon_id_data/', KYCProfilePolygonIdGetCreateUpdateDelete.as_view(), name='kyc_provider_polygon_id_get_create_update_delete'),
    path('required_schema/', KYCProfileRequiredSchemaView.as_view(), name='kyc_profile_required_schema_view')
]
