from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin)
from django.db import models
from commons.models import PrimaryUUIDTimeStampedModel
from django.utils.translation import gettext_lazy as _
from authentication.resources.constants import (
    AUTH_PROVIDERS, REGISTER_FAILED_MISSING_EMAIL,
    REGISTER_FAILED_MISSING_PASSWORD)
from phonenumber_field.modelfields import PhoneNumberField


class UserManager(BaseUserManager):

    def create_user(self, email, password):
        if email is None:
            raise ValueError(REGISTER_FAILED_MISSING_EMAIL)
        user = self.model(
            email=self.normalize_email(email))
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        if password is None:
            raise ValueError(REGISTER_FAILED_MISSING_PASSWORD)

        user = self.create_user(email=email, password=password)
        user.is_superuser = True
        user.is_admin = True
        user.is_staff = True
        user.is_verified = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PrimaryUUIDTimeStampedModel, PermissionsMixin):
    email = models.EmailField(verbose_name='email', max_length=255,
                              unique=True, db_index=True)  # validation at DB
    # phone_number = PhoneNumberField(_('Phone Number'), max_length=20)  # validation at frontend and backend
    is_admin = models.BooleanField(default=False)  # multiple admins
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)  # Only single superuser
    is_verified = models.BooleanField(default=False)
    auth_provider = models.CharField(max_length=255, blank=False,
                                     null=False, default=AUTH_PROVIDERS.get('email'))

    USERNAME_FIELD = AUTH_PROVIDERS.get('email')
    # REQUIRED_FIELDS = ['phone_number']

    objects = UserManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True

    def tokens(self):
        refresh = RefreshToken.for_user(self)
        return {
            'refresh_token': str(refresh),
            'access_token': str(refresh.access_token)
        }
