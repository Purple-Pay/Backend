from django.db import models
from commons.models import PrimaryUUIDTimeStampedModel
from authentication.models import User
from django.utils.translation import gettext_lazy as _


# Create your models here.
class PaymentType(PrimaryUUIDTimeStampedModel):
    name = models.CharField(_('payment type'), max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Id::{str(self.id)}::::Name::{str(self.name)}"


class BlockchainNetworkType(PrimaryUUIDTimeStampedModel):
    name = models.CharField(_('blockchain network'), max_length=100, blank=True, null=True)


class BlockchainNetwork(PrimaryUUIDTimeStampedModel):
    name = models.CharField(_('blockchain network'), max_length=100, blank=True, null=True)
    chain_id = models.CharField(_('chain id'), max_length=100, blank=True, null=True)
    network_type = models.ForeignKey(BlockchainNetworkType, on_delete=models.CASCADE, related_name="blockchain_network", blank=True, null=True)

    def __str__(self):
        return f"Id::{str(self.id)}::::Name::{str(self.name)}::::ChainId::{str(self.chain_id)}"


class CurrencyType(PrimaryUUIDTimeStampedModel):
    """ERC20, Fiat, Native"""
    name = models.CharField(_('currency type'), max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Id::{str(self.id)}::::Name::{str(self.name)}"


class Currency(PrimaryUUIDTimeStampedModel):
    name = models.CharField(_('currency'), max_length=100, blank=True, null=True)
    symbol_primary = models.CharField(_('symbol primary'), max_length=10, blank=True, null=True)
    symbol_aliases = models.CharField(_('symbol aliases'), max_length=100, blank=True, null=True)
    coingecko_id = models.CharField(_('coingecko id'), max_length=100, blank=True, null=True)
    currency_type = models.ForeignKey(CurrencyType, on_delete=models.CASCADE, related_name="currencies", blank=True, null=True)
    blockchain_network = models.ForeignKey(BlockchainNetwork, on_delete=models.CASCADE, related_name="currencies", blank=True, null=True)
    token_address_on_network = models.CharField(_('token address on network'), max_length=512, blank=True, null=True)
    decimals = models.IntegerField(blank=True, null=True)
    asset_url = models.CharField(_('Currency Logo'), max_length=512, blank=True, null=True)

    def __str__(self):
        return f"Id::{str(self.id)}::::Name::{str(self.name)}"


class PaymentStatus(PrimaryUUIDTimeStampedModel):
    name = models.CharField(_('Payment Status'), max_length=30, blank=True, null=True)

    def __str__(self):
        return f"Id::{str(self.id)}::::Name::{str(self.name)}"


class Payment(PrimaryUUIDTimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments")
    user_order_id = models.CharField(_('User Order Id'), max_length=200, blank=True, null=True)
    payment_type = models.ForeignKey(PaymentType, on_delete=models.CASCADE, related_name="payments")
    address_from = models.CharField(_('Address From'), max_length=200, blank=True, null=True)
    address_to = models.CharField(_('Address To'), max_length=200, blank=True, null=True)
    order_amount = models.FloatField()
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name="payments", blank=True, null=True)
    payment_status = models.ForeignKey(PaymentStatus, on_delete=models.CASCADE, related_name="payments",
                                       blank=True, null=True)
    transaction_hash = models.CharField(_('Transaction Hash'), max_length=512, blank=True, null=True)

    def __str__(self):
        return f"PaymentId::{str(self.id)}::::UserOrderId::{str(self.user_order_id)}"


# class BurnerContractDeployStatus(PrimaryUUIDTimeStampedModel):
#     """initiated deploy, not deploy, success deploy, failure deploy"""
#     name = models.CharField(_('Deployment Status Name'), max_length=200, blank=True, null=True)


class PaymentBurner(PrimaryUUIDTimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payment_burners")
    user_order_id = models.CharField(_('User Order Id'), max_length=200, blank=True, null=True)
    payment_type = models.ForeignKey(PaymentType, on_delete=models.CASCADE, related_name="payment_burners", blank=True, null=True)
    address_from = models.CharField(_('Address From'), max_length=200, blank=True, null=True)
    burner_address_to = models.CharField(_('Burner Address To'), max_length=200, blank=True, null=True)
    final_address_to = models.CharField(_('Final Address To'), max_length=200, blank=True, null=True)
    order_amount = models.FloatField(blank=True, null=True)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name="payment_burners", blank=True, null=True)
    payment_status = models.ForeignKey(PaymentStatus, on_delete=models.CASCADE, related_name="payment_burners", blank=True, null=True)
    transaction_hash = models.CharField(_('Transaction Hash'), max_length=512, blank=True, null=True)
    initial_block_number = models.CharField(_('Initial Block Number'), max_length=512, blank=True, null=True)
    transaction_block_number = models.CharField(_('Transaction Block Number'), max_length=512, blank=True, null=True)
    transaction_block_hash = models.CharField(_('Transaction Block Hash'), max_length=512, blank=True, null=True)
    blockchain_network = models.ForeignKey(BlockchainNetwork, on_delete=models.CASCADE, related_name="payment_burners",
                                           blank=True, null=True)
    description = models.CharField(_('Description'), max_length=512, blank=True, null=True)

    def __str__(self):
        return f"PaymentId::{str(self.id)}::::UserOrderId::{str(self.user_order_id)}"


class PaymentBurnerAddress(PrimaryUUIDTimeStampedModel):
    payment_id = models.ForeignKey(PaymentBurner, on_delete=models.CASCADE, related_name="payment_burner_addresses", blank=True, null=True)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name="payment_burner_addresses", blank=True, null=True)
    burner_address = models.CharField(_('burner address'), max_length=512, blank=True, null=True)
    order_amount = models.FloatField(blank=True, null=True)
    payment_status = models.ForeignKey(PaymentStatus, on_delete=models.CASCADE, related_name="payment_burner_addresses",
                                       blank=True, null=True)
    is_used_for_payment = models.BooleanField(default=False)

    transfer_to_merchant_transaction_hash = models.CharField(_('Transfer to Merchant Tx Hash'), max_length=512, blank=True, null=True)
    burner_contract_deploy_status = models.CharField(_('Burner Contract Deploy Status'), max_length=100, blank=True, null=True, default='not deploy')
    burner_contract_deploy_failure_reason = models.CharField(_('Deploy Fail Reason'), max_length=512, blank=True, null=True)
    # transaction_hash = models.CharField(_('Transaction Hash'), max_length=512, blank=True, null=True)

    def __str__(self):
        return f"BurnerAddressId::{str(self.id)}::::PaymentId::{str(self.payment_id)}"


class PurplePayFactoryContract(PrimaryUUIDTimeStampedModel):
    name = models.CharField(_('Purple Pay Factory Contract Name'), max_length=512, blank=True, null=True)
    address = models.CharField(_('Purple Pay Factory Contract Address'), max_length=512, blank=True, null=True)
    blockchain_network = models.ForeignKey(BlockchainNetwork, on_delete=models.CASCADE, related_name="purple_pay_factory_contract_addresses", blank=True, null=True)
    contract_abi = models.JSONField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    is_audited = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"Id::{str(self.id)}::::Name::{str(self.name)}::::Address::{str(self.address)}"


class PurplePayMultisigContract(PrimaryUUIDTimeStampedModel):
    name = models.CharField(_('Purple Pay Multisig Contract Name'), max_length=512, blank=True, null=True)
    address = models.CharField(_('Purple Pay Multisig Contract Address'), max_length=512, blank=True, null=True)
    blockchain_network = models.ForeignKey(BlockchainNetwork, on_delete=models.CASCADE, related_name="purple_pay_multisig_contract_addresses", blank=True, null=True)
    contract_abi = models.JSONField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    is_audited = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"Id::{str(self.id)}::::Name::{str(self.name)}::::Address::{str(self.address)}"


class PaymentSession(PrimaryUUIDTimeStampedModel):
    payment_id = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="payment_sessions")
    payment_status = models.ForeignKey(PaymentStatus, on_delete=models.CASCADE, related_name="payment_sessions")
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"PaymentSessionID::{str(self.id)}::::PaymentId::{str(self.payment_id)}"


class PaymentBurnerSample(PrimaryUUIDTimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payment_burner_samples", blank=True, null=True)
    user_order_id = models.CharField(_('User Order Id'), max_length=200, blank=True, null=True)
    payment_type = models.ForeignKey(PaymentType, on_delete=models.CASCADE, related_name="payment_burner_samples", blank=True, null=True)
    address_from = models.CharField(_('Address From'), max_length=200, blank=True, null=True)
    burner_address_to = models.CharField(_('Burner Address To'), max_length=200, blank=True, null=True)
    final_address_to = models.CharField(_('Final Address To'), max_length=200, blank=True, null=True)
    order_amount = models.FloatField(blank=True, null=True)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name="payment_burner_samples", blank=True, null=True)
    payment_status = models.ForeignKey(PaymentStatus, on_delete=models.CASCADE, related_name="payment_burner_samples", blank=True, null=True)
    transaction_hash = models.CharField(_('Transaction Hash'), max_length=512, blank=True, null=True)
    initial_block_number = models.CharField(_('Initial Block Number'), max_length=512, blank=True, null=True)
    transaction_block_number = models.CharField(_('Transaction Block Number'), max_length=512, blank=True, null=True)
    transaction_block_hash = models.CharField(_('Transaction Block Hash'), max_length=512, blank=True, null=True)
    blockchain_network = models.ForeignKey(BlockchainNetwork, on_delete=models.CASCADE, related_name="payment_burner_samples",
                                           blank=True, null=True)
    description = models.CharField(_('Description'), max_length=512, blank=True, null=True)

    def __str__(self):
        return f"PaymentId::{str(self.id)}::::UserOrderId::{str(self.user_order_id)}"


class PaymentBurnerAddressSample(PrimaryUUIDTimeStampedModel):
    payment_id = models.ForeignKey(PaymentBurnerSample, on_delete=models.CASCADE, related_name="payment_burner_address_samples", blank=True, null=True)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name="payment_burner_sample_addresses", blank=True, null=True)
    burner_address = models.CharField(_('burner address'), max_length=512, blank=True, null=True)
    order_amount = models.FloatField(blank=True, null=True)
    payment_status = models.ForeignKey(PaymentStatus, on_delete=models.CASCADE, related_name="payment_burner_address_samples",
                                       blank=True, null=True)
    is_used_for_payment = models.BooleanField(default=False)

    transfer_to_merchant_transaction_hash = models.CharField(_('Transfer to Merchant Tx Hash'), max_length=512, blank=True, null=True)
    burner_contract_deploy_status = models.CharField(_('Burner Contract Deploy Status'), max_length=100, blank=True, null=True, default='not deploy')
    burner_contract_deploy_failure_reason = models.CharField(_('Deploy Fail Reason'), max_length=512, blank=True, null=True)
    # transaction_hash = models.CharField(_('Transaction Hash'), max_length=512, blank=True, null=True)

    def __str__(self):
        return f"BurnerAddressId::{str(self.id)}::::PaymentId::{str(self.payment_id)}"
