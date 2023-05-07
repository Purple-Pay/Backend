from .models import KYCProfile, KYCProvider, KYCProfilePolygonId, KYCProfileRequiredSchema
from authentication.models import User
from rest_framework import serializers


class KYCProviderSerializer(serializers.ModelSerializer):

    class Meta:
        model = KYCProvider
        fields = '__all__'


class KYCProfileSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    kyc_provider = serializers.PrimaryKeyRelatedField(queryset=KYCProvider.objects.all(), write_only=True)

    class Meta:
        model = KYCProfile
        fields = '__all__'


class KYCProfileClaimRequestSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    kyc_provider = serializers.PrimaryKeyRelatedField(queryset=KYCProvider.objects.all(), write_only=True)

    class Meta:
        model = KYCProfile
        fields = '__all__'


class KYCProfilePolygonIdSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    kyc_profile = serializers.PrimaryKeyRelatedField(queryset=KYCProfile.objects.all())

    class Meta:
        model = KYCProfilePolygonId
        fields = '__all__'


class KYCProfileRequiredSchemaSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = KYCProfileRequiredSchema
        fields = '__all__'
