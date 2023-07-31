from django.db import models
from commons.models import PrimaryUUIDTimeStampedModel
from authentication.models import User
from django.utils.translation import gettext_lazy as _


# Create your models here.
class APIKey(PrimaryUUIDTimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="api_keys")
    key_name = models.CharField(_('API Key Name'), max_length=512, blank=True, null=True)

    def __str__(self):
        return f"APIKey::{str(self.id)}::::UserId::{str(self.user)}"
