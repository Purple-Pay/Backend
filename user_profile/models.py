from django.db import models
from commons.models import PrimaryUUIDTimeStampedModel
from authentication.models import User
from django.utils.translation import gettext_lazy as _
from payments.models import BlockchainNetwork, Currency
from django.contrib.postgres.fields import ArrayField


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
    default_network = models.ForeignKey(BlockchainNetwork, on_delete=models.SET_NULL,
                                        related_name="user_profiles", null=True, blank=True)

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

    def __str__(self):
        return f"Id::{str(self.id)}::::UserId::{str(self.user)}"


class Webhook(PrimaryUUIDTimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="webhooks", null=True, blank=True)
    url = models.CharField(_('webhook'), max_length=512, blank=True, null=True)
    status = models.CharField(_('webhook status'), max_length=50, blank=True, null=True)    # ACTIVE, INACTIVE
    secret_key = models.CharField(_('secret key'), max_length=1024, blank=True, null=True)
    event_type = models.CharField(_('events of interest'), max_length=128, blank=True, null=True)    # 'PAYMENT_SUCCESS', 'REFUND', 'CHARGEBACK"
    retry_count = models.IntegerField(default=2)
    payload_format = models.JSONField(blank=True, null=True)
    delivery_response_format = models.JSONField(blank=True, null=True)
    version = models.CharField(_('version'), max_length=32, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True)    # IP Whitelisting


class WebhookActivity(PrimaryUUIDTimeStampedModel):
    webhook_id = models.ForeignKey(Webhook, on_delete=models.SET_NULL, blank=True, null=True, related_name="webhookactivity")
    latest_interaction = models.DateTimeField(auto_now=True)
    latest_interaction_type = models.CharField(_('latest interaction type'), max_length=64, blank=True, null=True)    # 'SUCCESS', 'FAIL'
    delivery_response_body = models.CharField(_('webhook delivery response'), max_length=1024, blank=True, null=True)
    delivery_response_status_code = models.CharField(_('webhook delivery response status'), max_length=64, blank=True, null=True)
    error_log = models.TextField(blank=True, null=True)







