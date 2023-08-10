from django.urls import path
from .views import (
    PaymentTypeListCreate, PaymentTypeRetrieveUpdateDelete,
    CurrencyListCreate, CurrencyRetrieveUpdateDelete,
    PaymentStatusListCreate, PaymentStatusRetrieveUpdateDelete,
    PaymentList, PaymentFilter,
    PaymentBurnerAddressGetCreateUpdate3, PaymentBurnerAddressVerifyDetail4,
    PaymentBurnerAddressSampleGetCreateUpdate, PaymentBurnerAddressSampleVerifyDetail,
    ChainConfigGet, PaymentConfig, PaymentListExternal, PaymentFilterExternal
)
from django.views.decorators.csrf import csrf_exempt

from django.urls import path
from .views import ChainConfigGet


urlpatterns = [
    path('chain_config/', ChainConfigGet.as_view(), name='chain_config_get'),
    path('config/', PaymentConfig.as_view(), name='payment_config_get'),
    path('payment_type/', PaymentTypeListCreate.as_view(), name='payment_type_list_create'),
    path('payment_type/<str:id>', PaymentTypeRetrieveUpdateDelete.as_view(), name='payment_type_get_update_delete'),
    path('currency/', CurrencyListCreate.as_view(), name='currency_list_create'),
    path('currency/<str:id>', CurrencyRetrieveUpdateDelete.as_view(), name='currency_get_update_delete'),
    path('payment_status/', PaymentStatusListCreate.as_view(), name='payment_status_list_create'),
    path('payment_status/<str:id>', PaymentStatusRetrieveUpdateDelete.as_view(),
         name='payment_status_get_update_delete'),

    path('list/', PaymentList.as_view(), name='payment_list'),
    path('filter/', PaymentFilter.as_view(), name='payment_filter'),
    path('all/<str:apiKey>', PaymentListExternal.as_view(), name='payment_list_external'),
    path('dateFilter/<str:apiKey>', PaymentFilterExternal.as_view(), name='payment_filter_external'),

    path('burner_address/', csrf_exempt(PaymentBurnerAddressGetCreateUpdate3.as_view()),
         name='burner_payment_get_create_update'),
    path('burner_address/payment_verify/<str:payment_id>', PaymentBurnerAddressVerifyDetail4.as_view(),
         name='payment_burner_address_verify_detail'),
    path('burner_address/sample/', csrf_exempt(PaymentBurnerAddressSampleGetCreateUpdate.as_view()),
         name='burner_payment_sample_get_create_update'),
    path('burner_address/sample/payment_verify/<str:payment_id>', PaymentBurnerAddressSampleVerifyDetail.as_view(),
         name='payment_burner_address_sample_verify_detail'),

    # path('', PaymentGetCreateUpdate.as_view(), name='payment_get_create_update'),
    # path('session/', PaymentSessionGetCreateUpdate.as_view(), name='payment_session_get_create_update'),
    # path('session/<str:session_id>', PaymentSessionGetDetail.as_view(), name='payment_session_get_detail'),
    # path('payment_verify/<str:payment_id>', PaymentVerifyDetail.as_view(), name='payment_verify_detail'),

]
