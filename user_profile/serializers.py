from .models import UserProfile, UserType, UserSmartContractWalletAddress
from payments.models import BlockchainNetwork, Currency
from authentication.models import User
from rest_framework import serializers


class UserProfileSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = UserProfile
        fields = '__all__'


class UserTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserType
        fields = '__all__'


class UserSmartContractWalletAddressSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    blockchain_network = serializers.PrimaryKeyRelatedField(queryset=BlockchainNetwork.objects.all())
    currency = serializers.PrimaryKeyRelatedField(queryset=Currency.objects.all())

    class Meta:
        model = UserSmartContractWalletAddress
        fields = '__all__'
