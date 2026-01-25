from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import random
from itertools import chain
from operator import attrgetter
import pycountry
import uuid


# then your models here


COUNTRY_CHOICES = [(country.name, country.name) for country in pycountry.countries]



GENDER_CHOICES = [
    ('M', 'Male'),
    ('F', 'Female'),
    ('O', 'Other'),
]









class CustomUser(AbstractUser):
    is_locked = models.BooleanField(default=False)
    is_transfer_locked = models.BooleanField(default=False) 
    email = models.EmailField(unique=True)
    verification_code = models.CharField(max_length=6, blank=True, null=True)
    verification_code_expired = models.BooleanField(default=False)
    verification_code_sent_at = models.DateTimeField(blank=True, null=True)  # optional timestamp

    # -------------------------
    def is_code_expired(self):
        """
        Returns True if the verification code is expired.
        Uses verification_code_expired flag or 5-min timeout.
        """
        # If the explicit expired flag is True
        if self.verification_code_expired:
            return True

        # If using timestamp to expire after 5 minutes
        if self.verification_code_sent_at:
            return timezone.now() > self.verification_code_sent_at + timedelta(minutes=5)

        # If no code was ever sent, treat as expired
        return True

    # -------------------------
    def get_transaction_history(self):
        deposits = self.deposits.all().annotate(
            transaction_type=models.Value('credit', output_field=models.CharField()),
            description=models.Value('Deposit', output_field=models.CharField()),
        )

        transfers = self.sent_transfers.all().annotate(
            transaction_type=models.Case(
                models.When(status='F', then=models.Value('declined')),
                models.When(status='P', then=models.Value('pending')),
                default=models.Value('debit'),  # status = 'S'
                output_field=models.CharField()
            ),
            description=models.Case(
                models.When(status='S', then=models.Value('Debited')),
                models.When(status='F', code_entered=True, then=models.Value('Fail Debited')),
                models.When(status='F', code_entered=False, then=models.Value('Failed')),
                models.When(status='P', then=models.Value('Transfer Pending')),
                default=models.Value('Transfer'),
                output_field=models.CharField()
            )
        )

        transactions = sorted(
            chain(deposits, transfers),
            key=attrgetter('timestamp'),
            reverse=True
        )

        return transactions

    # -------------------------
    def __str__(self):
        return f"{self.username} ({self.email})"










def generate_unique_account_number():
    while True:
        number = str(random.randint(10**9, 10**10 - 1))  # 10-digit number
        if not Account.objects.filter(account_number=number).exists():
            return number


class Account(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='account')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=12, null=True, blank=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    street = models.CharField(max_length=255)
    apt_suite = models.CharField(max_length=10)
    city = models.CharField(max_length=10)
    state = models.CharField(max_length=20)
    zip_code = models.CharField(max_length=6)
    nationality = models.CharField(max_length=100, choices=COUNTRY_CHOICES, blank=True, null=True)
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES, blank=True, null=True)
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    account_number = models.CharField(max_length=10, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.account_number:
            self.account_number = generate_unique_account_number()
        super().save(*args, **kwargs)  # move this outside the `if` block

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.account_number}"







class Transfer(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_transfers')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_transfers', null=True, blank=True)
    external_receiver_email = models.EmailField(null=True, blank=True)
    receiver_name = models.CharField(max_length=255, null=True, blank=True)
    account = models.CharField(max_length=20)
    swift_code = models.CharField(max_length=20, blank=True, null=True)
    receiver_bank = models.CharField(max_length=255)
    receiver_account = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    recipient_address = models.CharField(max_length=255, null=True, blank=True)
    # iban = models.CharField(max_length=34, null=True, blank=True)
    code_entered = models.BooleanField(default=False) 
    state = models.CharField(max_length=20, blank=True, null=True)
    nationality = models.CharField(max_length=100, choices=COUNTRY_CHOICES, blank=True, null=True)
    zip_code = models.CharField(max_length=6, blank=True, null=True)
    city = models.CharField(max_length=20, blank=True, null=True)
    verification_code = models.CharField(max_length=6, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    timestamp = models.DateTimeField(default=timezone.now)
    reference = models.CharField(max_length=100, blank=True, null=True, unique=True)
    status_choices = [
    ('P', 'Pending'),
    ('S', 'Successful'),
    ('F', 'Failed'),
]

    status = models.CharField(max_length=1, choices=status_choices, default='P')
    purpose = models.TextField(null=True, blank=True)

    def __str__(self):
        if self.receiver:
            return f"Transfer from {self.sender} to {self.receiver}"
        return f"Transfer from {self.sender} to External ({self.receiver_account or 'N/A'})"
    # =======================================================
    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = str(uuid.uuid4())[:8]  # generate short unique ref id
        super().save(*args, **kwargs)



class Deposit(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='deposits')
    bank_name = models.CharField(max_length=255)
    address = models.CharField(max_length=225, default='Unknown', null=True, blank=True)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    timestamp = models.DateTimeField(default=timezone.now)
    method = models.CharField(max_length=100, default='Manual')  # e.g., Card, Admin, Bank, etc.
    reference = models.CharField(max_length=100, blank=True, null=True, unique=True)
    purpose = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Deposit of {self.amount} by {self.user}"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        if not self.reference:
            self.reference = str(uuid.uuid4())[:8]
        super().save(*args, **kwargs)
        if is_new:
            account = self.user.account
            account.balance += self.amount
            account.save()












