import uuid
from django.db import models


class TimeStampedModel(models.Model):
    """
    auto_now_add field is only updated when the row or object is created
    auto_now field is updated every time a row is updated
    """
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta(object):
        abstract = True


class PrimaryUUIDModel(models.Model):
    """
    uuid.uuid1 may compromise privacy since it creates a UUID containing the computer's network address
    hence using uuid.uuid4
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta(object):
        abstract = True


class PrimaryUUIDTimeStampedModel(PrimaryUUIDModel, TimeStampedModel):
    class Meta(object):
        abstract = True
