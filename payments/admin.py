from django.contrib import admin
from .models import (Payment, PaymentStatus, PaymentType, Currency,
                     CurrencyType, BlockchainNetwork, PaymentBurner,
                     PaymentBurnerAddress, PurplePayFactoryContract,
                     PurplePayMultisigContract)


admin.site.register(Payment)
admin.site.register(PaymentStatus)
admin.site.register(PaymentType)
admin.site.register(Currency)
admin.site.register(CurrencyType)
admin.site.register(BlockchainNetwork)
admin.site.register(PaymentBurner)
admin.site.register(PaymentBurnerAddress)
admin.site.register(PurplePayFactoryContract)
admin.site.register(PurplePayMultisigContract)

