from django.db import models
from commons.models import PrimaryUUIDTimeStampedModel
from authentication.models import User
from django.utils.translation import gettext_lazy as _


class KYCProvider(PrimaryUUIDTimeStampedModel):
    name = models.CharField(_('name'), max_length=30, blank=True, null=True)   # Synaps, Idify

    def __str__(self):
        return f"Id::{str(self.id)}::::Name::{str(self.name)}"


class KYCProfile(PrimaryUUIDTimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="kyc_profile")
    first_name = models.CharField(_('first name'), max_length=30, blank=True, null=True)
    middle_name = models.CharField(_('middle name'), max_length=30, blank=True, null=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True, null=True)
    location = models.CharField(_('location'), max_length=150, blank=True, null=True)
    id_proof_url = models.TextField(_('id proof url'), max_length=1000, blank=True, null=True)
    kyc_verification_status = models.CharField(_('verification status'), max_length=100, blank=True, null=True)
    kyc_provider = models.ForeignKey(KYCProvider, on_delete=models.CASCADE, related_name="kyc_profile")

    def __str__(self):
        return f"ProfileId::{str(self.id)}::::UserId::{str(self.user)}::Name::{str(self.first_name)}"


class KYCProfilePolygonId(PrimaryUUIDTimeStampedModel):
    kyc_profile = models.ForeignKey(KYCProfile, on_delete=models.CASCADE, related_name="kyc_profile")
    polygon_id_offer_response = models.JSONField()
    polygon_id_offer_qr_code_response = models.JSONField()

    def __str__(self):
        return f"PolygonId::{str(self.id)}::::KYCProfileId::{str(self.kyc_profile)}"


class KYCProfileRequiredSchema(PrimaryUUIDTimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="kyc_profile_required_schema")
    schema_id = models.CharField(_('schema id'), max_length=1000, blank=True, null=True)

    def __str__(self):
        return f"Id::{str(self.id)}::::UserId::{str(self.user)}::SchemaId::{str(self.schema_id)}"
