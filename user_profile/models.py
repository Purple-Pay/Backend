from django.db import models
from commons.models import PrimaryUUIDTimeStampedModel
from authentication.models import User
from django.utils.translation import gettext_lazy as _
from payments.models import BlockchainNetwork, Currency


# Create your models here.
class UserType(PrimaryUUIDTimeStampedModel):
    name = models.CharField(_('name'), max_length=50, blank=True, null=True)

    def __str__(self):
        return f"Id::{str(self.id)}::::Name::{str(self.name)}"


class UserProfile(PrimaryUUIDTimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="user_profile")
    profile_image = models.TextField(_('profile image'), max_length=300, blank=True, null=True)
    first_name = models.CharField(_('first name'), max_length=30, blank=True, null=True)
    middle_name = models.CharField(_('middle name'), max_length=30, blank=True, null=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True, null=True)
    location = models.CharField(_('location'), max_length=100, blank=True, null=True)
    company = models.CharField(_('company'), max_length=100, blank=True, null=True)
    user_type = models.ForeignKey(UserType, on_delete=models.CASCADE, related_name="user_profiles")
    agreed_terms_and_conditions = models.BooleanField(default=False)
    agreed_privacy_policy = models.BooleanField(default=False)
    user_wallet_address = models.CharField(_('wallet_address'), max_length=300, blank=True, null=True)
    user_smart_contract_wallet_address = models.CharField(_('smart_contract_wallet_address'), max_length=300,
                                                          blank=True, null=True)
    company_url = models.CharField(_('company_url'), max_length=512, blank=True, null=True)

    def __str__(self):
        return f"Id::{str(self.id)}::::UserId::{str(self.user)}::::UserType::{str(self.user_type)}"


class UserSmartContractWalletAddress(PrimaryUUIDTimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_scw_addresses")
    user_wallet_address = models.CharField(_('wallet_address'), max_length=300, blank=True, null=True)
    user_smart_contract_wallet_address = models.CharField(_('smart_contract_wallet_address'), max_length=512,
                                                          blank=True, null=True)
    blockchain_network = models.ForeignKey(BlockchainNetwork, on_delete=models.CASCADE,
                                           related_name="user_scw_addresses",
                                           blank=True, null=True)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE,
                                 related_name="user_scw_addresses",
                                 blank=True, null=True)

    def __str__(self):
        return f"Id::{str(self.id)}::::UserId::{str(self.user)}"

