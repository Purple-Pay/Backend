from .models import UserProfile, UserType, UserSmartContractWalletAddress, Webhook, WebhookActivity
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


    class Meta:
        model = UserSmartContractWalletAddress
        fields = '__all__'


class WebhookSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    modified_at = serializers.DateTimeField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Webhook
        fields = '__all__'


class WebhookActivitySerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    modified_at = serializers.DateTimeField(read_only=True)
    webhook_id = serializers.PrimaryKeyRelatedField(queryset=Webhook.objects.all())

    class Meta:
        model = WebhookActivity
        fields = '__all__'
