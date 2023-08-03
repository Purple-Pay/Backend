from .models import (
    PaymentType, Currency, Payment, PaymentSession, PaymentStatus, BlockchainNetwork, BlockchainNetworkType,
    PaymentBurner, PaymentBurnerAddress, PaymentBurnerSample, PaymentBurnerAddressSample)
from rest_framework import serializers
from authentication.models import User
from datetime import datetime, timedelta


class PaymentTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = PaymentType
        fields = '__all__'


class PaymentStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = PaymentStatus
        fields = '__all__'


class CurrencySerializer(serializers.ModelSerializer):

    class Meta:
        model = Currency
        fields = '__all__'


class BlockchainNetworkSerializer(serializers.ModelSerializer):

    class Meta:
        model = BlockchainNetwork
        fields = '__all__'


class BlockchainNetworkTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = BlockchainNetworkType
        fields = '__all__'


class PaymentSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True)
    payment_type = serializers.PrimaryKeyRelatedField(queryset=PaymentType.objects.all())
    currency = serializers.PrimaryKeyRelatedField(queryset=Currency.objects.all())

    class Meta:
        model = Payment
        fields = "__all__"


class PaymentBurnerSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = PaymentBurner
        fields = "__all__"


class PaymentBurnerAddressSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = PaymentBurnerAddress
        fields = "__all__"


class PaymentBurnerSampleSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = PaymentBurnerSample
        fields = "__all__"


class PaymentBurnerAddressSampleSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = PaymentBurnerAddressSample
        fields = "__all__"


class PaymentSessionSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    payment_id = serializers.PrimaryKeyRelatedField(queryset=Payment.objects.all())
    payment_status = serializers.PrimaryKeyRelatedField(queryset=PaymentStatus.objects.all())
    expires_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = PaymentSession
        fields = '__all__'
