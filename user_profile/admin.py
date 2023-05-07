from django.contrib import admin
from .models import UserProfile, UserType, UserSmartContractWalletAddress


admin.site.register(UserProfile)
admin.site.register(UserType)
admin.site.register(UserSmartContractWalletAddress)
