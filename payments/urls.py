from django.urls import path
from .views import (
    PaymentTypeListCreate, PaymentTypeRetrieveUpdateDelete,
    CurrencyListCreate, CurrencyRetrieveUpdateDelete,
    PaymentStatusListCreate, PaymentStatusRetrieveUpdateDelete,
    PaymentGetCreateUpdate, PaymentSessionGetCreateUpdate,
    PaymentVerifyDetail, PaymentSessionGetDetail,
    PaymentList, PaymentFilter,
    PaymentBurnerAddressGetCreateUpdate, PaymentBurnerAddressVerifyDetail3
)

urlpatterns = [
    path('payment_type/', PaymentTypeListCreate.as_view(), name='payment_type_list_create'),
    path('payment_type/<str:id>', PaymentTypeRetrieveUpdateDelete.as_view(), name='payment_type_get_update_delete'),
    path('currency/', CurrencyListCreate.as_view(), name='currency_list_create'),
    path('currency/<str:id>', CurrencyRetrieveUpdateDelete.as_view(), name='currency_get_update_delete'),
    path('payment_status/', PaymentStatusListCreate.as_view(), name='payment_status_list_create'),
    path('payment_status/<str:id>', PaymentStatusRetrieveUpdateDelete.as_view(),
         name='payment_status_get_update_delete'),
    path('', PaymentGetCreateUpdate.as_view(), name='payment_get_create_update'),
    path('list/', PaymentList.as_view(), name='payment_list'),
    # path('session/', PaymentSessionGetCreateUpdate.as_view(), name='payment_session_get_create_update'),
    # path('session/<str:session_id>', PaymentSessionGetDetail.as_view(), name='payment_session_get_detail'),
    path('payment_verify/<str:payment_id>', PaymentVerifyDetail.as_view(), name='payment_verify_detail'),
    path('filter/', PaymentFilter.as_view(), name='payment_filter'),

    path('burner_address/', PaymentBurnerAddressGetCreateUpdate.as_view(), name='burner_payment_get_create_update'),
    path('burner_address/payment_verify/<str:payment_id>', PaymentBurnerAddressVerifyDetail3.as_view(),
         name='payment_burner_address_verify_detail'),

]
