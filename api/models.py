import uuid
import random
from datetime import timedelta
from itertools import chain
from operator import attrgetter

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser

import pycountry


def generate_6_digit_code():
    return f"{random.randint(100000, 999999)}"


COUNTRY_CHOICES = [(c.name, c.name) for c in pycountry.countries]
GENDER_CHOICES = [("M", "Male"), ("F", "Female"), ("O", "Other")]


# ========================= USER =========================
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)

    is_locked = models.BooleanField(default=False)
    is_transfer_locked = models.BooleanField(default=False)

    verification_code = models.CharField(max_length=6, blank=True, null=True)
    verification_code_sent_at = models.DateTimeField(blank=True, null=True)

    def is_code_expired(self):
        return (
            not self.verification_code_sent_at
            or timezone.now() > self.verification_code_sent_at + timedelta(minutes=5)
        )

    def clear_verification_code(self):
        self.verification_code = None
        self.verification_code_sent_at = None
        self.save(update_fields=["verification_code", "verification_code_sent_at"])

    def get_transaction_history(self):
        deposits = self.deposits.all().annotate(
            transaction_type=models.Value("credit", output_field=models.CharField()),
            description=models.Value("Deposit", output_field=models.CharField()),
        )

        transfers = self.sent_transfers.all().annotate(
            transaction_type=models.Case(
                models.When(status="F", then=models.Value("declined")),
                models.When(status="P", then=models.Value("pending")),
                default=models.Value("debit"),
                output_field=models.CharField(),
            ),
            description=models.Value("Transfer", output_field=models.CharField()),
        )

        return sorted(
            chain(deposits, transfers), key=attrgetter("timestamp"), reverse=True
        )

    def __str__(self):
        return self.email


# ========================= ACCOUNT =========================
def generate_unique_account_number():
    while True:
        num = str(random.randint(10**9, 10**10 - 1))
        if not Account.objects.filter(account_number=num).exists():
            return num


class Account(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="account"
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=12, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    street = models.CharField(max_length=255)
    apt_suite = models.CharField(max_length=20)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=10)
    nationality = models.CharField(
        max_length=100, choices=COUNTRY_CHOICES, blank=True, null=True
    )
    gender = models.CharField(
        max_length=6, choices=GENDER_CHOICES, blank=True, null=True
    )
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    account_number = models.CharField(max_length=10, unique=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.account_number:
            self.account_number = generate_unique_account_number()
        super().save(*args, **kwargs)
        AccountSecurity.objects.get_or_create(account=self)
        TransactionSettings.objects.get_or_create(account=self)  # per-account settings

    def __str__(self):
        return self.account_number


# ========================= SECURITY =========================
# class TransactionSettings(models.Model):
#     enable_activation_code = models.BooleanField(default=False)
#     enable_tax_code = models.BooleanField(default=False)
#     enable_imf_code = models.BooleanField(default=False)

#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return "Transaction Security Settings"


class TransactionSettings(models.Model):
    account = models.OneToOneField(
        "Account", on_delete=models.CASCADE, related_name="transaction_settings"
    )

    enable_transaction_code = models.BooleanField(
        default=True
    )  # Controls if we enable other codes
    enable_tax_code = models.BooleanField(default=False)
    enable_activation_code = models.BooleanField(default=False)
    enable_imf_code = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Auto-enable other codes if transaction code is enabled
        if self.enable_transaction_code:
            self.enable_tax_code = True
            self.enable_activation_code = True
            self.enable_imf_code = True
        else:
            # If transaction code is disabled, enable only email OTP for transfer
            self.enable_tax_code = False
            self.enable_activation_code = False
            self.enable_imf_code = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Transaction Settings for {self.account.account_number}"


# class AccountSecurity(models.Model):
#     account = models.OneToOneField(
#         Account, on_delete=models.CASCADE, related_name="security"
#     )

#     activation_code = models.CharField(max_length=6, blank=True, null=True)
#     tax_code = models.CharField(max_length=6, blank=True, null=True)
#     imf_code = models.CharField(max_length=6, blank=True, null=True)

#     verified_devices = models.JSONField(default=dict)
#     updated_at = models.DateTimeField(auto_now=True)

#     def generate_code(self, code_type):
#         code = generate_6_digit_code()
#         setattr(self, f"{code_type}_code", code)
#         self.save(update_fields=[f"{code_type}_code"])
#         return code

#     def is_code_verified(self, code_type, device_id):
#         return code_type in self.verified_devices.get(device_id, [])

#     def mark_code_verified(self, code_type, device_id):
#         self.verified_devices.setdefault(device_id, [])
#         if code_type not in self.verified_devices[device_id]:
#             self.verified_devices[device_id].append(code_type)
#         self.save(update_fields=["verified_devices"])

#     def clear_codes(self):
#         self.tax_code = None
#         self.activation_code = None
#         self.imf_code = None
#         self.verified_devices = {}
#         self.save()

# class AccountSecurity(models.Model):
#     account = models.OneToOneField(
#         Account, on_delete=models.CASCADE, related_name="security"
#     )

#     activation_code = models.CharField(max_length=6, blank=True, null=True)
#     tax_code = models.CharField(max_length=6, blank=True, null=True)
#     imf_code = models.CharField(max_length=6, blank=True, null=True)

#     verified_devices = models.JSONField(default=dict)
#     updated_at = models.DateTimeField(auto_now=True)

#     def generate_code(self, code_type):
#         """Generate and store a 6-digit code for the given type."""
#         code = generate_6_digit_code()
#         setattr(self, f"{code_type}_code", code)
#         self.save(update_fields=[f"{code_type}_code"])
#         return code

#     def is_code_verified(self, code_type, device_id):
#         """Check if a code is already verified for a device."""
#         return code_type in self.verified_devices.get(device_id, [])

#     def mark_code_verified(self, code_type, device_id):
#         """Mark a code as verified for a device."""
#         self.verified_devices.setdefault(device_id, [])
#         if code_type not in self.verified_devices[device_id]:
#             self.verified_devices[device_id].append(code_type)
#             self.save(update_fields=["verified_devices"])

#     # ✅ Add this method so backend won't crash
#     def clear_codes(self, device_id=None):
#         """
#         Clear all codes and verified devices if all enabled codes
#         have been verified for the given device.
#         """
#         CODE_ORDER = ["tax", "activation", "imf"]
#         all_verified = True

#         settings_obj = self.account.transaction_settings

#         for code in CODE_ORDER:
#             if getattr(settings_obj, f"enable_{code}_code", False):
#                 if device_id and not self.is_code_verified(code, device_id):
#                     all_verified = False
#                     break

#         if all_verified:
#             self.tax_code = None
#             self.activation_code = None
#             self.imf_code = None
#             self.verified_devices = {}
#             self.save()

class AccountSecurity(models.Model):
    account = models.OneToOneField(
        Account, on_delete=models.CASCADE, related_name="security"
    )

    # Store codes for multi-step transfer verification
    activation_code = models.CharField(max_length=6, blank=True, null=True)
    tax_code = models.CharField(max_length=6, blank=True, null=True)
    imf_code = models.CharField(max_length=6, blank=True, null=True)

    # Track which codes were verified per device
    verified_devices = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)

    def generate_code(self, code_type):
        """Generate and store a 6-digit code for the given type."""
        code = generate_6_digit_code()
        setattr(self, f"{code_type}_code", code)
        self.save(update_fields=[f"{code_type}_code"])
        return code

    def is_code_verified(self, code_type, device_id):
        """Check if a code is already verified for a device."""
        return code_type in self.verified_devices.get(device_id, [])

    def mark_code_verified(self, code_type, device_id):
        """Mark a code as verified for a device."""
        self.verified_devices.setdefault(device_id, [])
        if code_type not in self.verified_devices[device_id]:
            self.verified_devices[device_id].append(code_type)
            self.save(update_fields=["verified_devices"])

    def get_next_code(self, transaction_settings, device_id):
        """
        Returns the next required code for a device according to CODE_ORDER:
        tax -> activation -> imf
        """
        CODE_ORDER = ["tax", "activation", "imf"]
        for code in CODE_ORDER:
            if getattr(transaction_settings, f"enable_{code}_code", False):
                if not self.is_code_verified(code, device_id):
                    return code
        return None

    def clear_codes_if_all_verified(self, transaction_settings, device_id):
        """
        Clear all codes and verified devices only if all enabled codes
        have been verified for this device.
        """
        CODE_ORDER = ["tax", "activation", "imf"]
        all_verified = True
        for code in CODE_ORDER:
            if getattr(transaction_settings, f"enable_{code}_code", False):
                if not self.is_code_verified(code, device_id):
                    all_verified = False
                    break

        if all_verified:
            self.tax_code = None
            self.activation_code = None
            self.imf_code = None
            self.verified_devices = {}
            self.save()

    def clear_codes(self, device_id=None):
        """
        Force clear all codes and verified devices.
        If device_id is provided, clears only for that device.
        Otherwise, clears everything.
        """
        self.tax_code = None
        self.activation_code = None
        self.imf_code = None

        if device_id:
            # Clear only this device
            if device_id in self.verified_devices:
                del self.verified_devices[device_id]
        else:
            # Clear all devices
            self.verified_devices = {}

        self.save()

# ========================= TRANSFER =========================
class Transfer(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_transfers",
    )
    receiver_name = models.CharField(max_length=255)
    receiver_bank = models.CharField(max_length=255)
    receiver_account = models.CharField(max_length=30)
    iban = models.CharField(max_length=34, blank=True, null=True)  # ✅ IBAN
    swift_code = models.CharField(max_length=11, blank=True, null=True)  # ✅ SWIFT/BIC
    recipient_address = models.CharField(max_length=255, blank=True, null=True)
    purpose = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    reference = models.CharField(max_length=12, unique=True, blank=True)
    status = models.CharField(
        max_length=1,
        choices=[("P", "Pending"), ("S", "Success"), ("F", "Failed")],
        default="P",
    )
    timestamp = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = uuid.uuid4().hex[:10].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.reference


# ========================= DEPOSIT =========================
class Deposit(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="deposits"
    )
    bank_name = models.CharField(max_length=255)
    address = models.CharField(max_length=225, blank=True, null=True)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    timestamp = models.DateTimeField(default=timezone.now)
    reference = models.CharField(max_length=100, unique=True, blank=True)

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        if not self.reference:
            self.reference = uuid.uuid4().hex[:8]
        super().save(*args, **kwargs)
        if is_new:
            acc = self.user.account
            acc.balance += self.amount
            acc.save()
