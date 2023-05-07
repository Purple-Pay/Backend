from .models import APIKey
from rest_framework import serializers
from authentication.models import User


class APIKeySerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = APIKey
        fields = '__all__'
