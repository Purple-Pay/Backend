from django.db import models
from commons.models import PrimaryUUIDTimeStampedModel
from authentication.models import User
from django.utils.translation import gettext_lazy as _


# Create your models here.
class APIKey(PrimaryUUIDTimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="api_keys")

    def __str__(self):
        return str(self.id) + "::" + str(self.user)
