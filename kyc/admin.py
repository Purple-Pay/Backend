from django.contrib import admin
from .models import KYCProvider, KYCProfile, KYCProfilePolygonId, KYCProfileRequiredSchema


admin.site.register(KYCProfile)
admin.site.register(KYCProvider)
admin.site.register(KYCProfilePolygonId)
admin.site.register(KYCProfileRequiredSchema)