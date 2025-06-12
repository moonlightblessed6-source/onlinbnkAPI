from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone


# then your models here


COUNTRY_CHOICES = [
    ('US', 'United States'),
    
]

GENDER_CHOICES = [
    ('M', 'Male'),
    ('F', 'Female'),
    ('O', 'Other'),
]

class CustomUser(AbstractUser):
    is_locked = models.BooleanField(default=False)
    email = models.EmailField(unique=True)

class Account(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='account')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=12, null=True, blank=True)
    email = models.EmailField(unique=True)
    nationality = models.CharField(max_length=100, choices=COUNTRY_CHOICES, blank=True, null=True)
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES, blank=True, null=True)
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"







class Transfer(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_transfers')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_transfers', null=True, blank=True)
    external_receiver_email = models.EmailField(null=True, blank=True)
    external_receiver_name = models.CharField(max_length=255, null=True, blank=True)
    account = models.CharField(max_length=20)
    address = models.CharField(max_length=225, default='Unknown', null=True, blank=True)
    bank_name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    verification_code = models.CharField(max_length=6, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    timestamp = models.DateTimeField(default=timezone.now)
    status_choices = [
        ('P', 'Pending'),
        ('S', 'Successful'),
        ('F', 'Failed'),
    ]
    status = models.CharField(max_length=1, choices=status_choices, default='P')
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        if self.receiver:
            return f'Transfer from {self.sender} to {self.receiver} - {self.amount}'
        else:
            return f'Transfer from {self.sender} to external {self.external_receiver_email or self.external_receiver_name} - {self.amount}'







# class Deposit(models.Model):
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='deposits')
#     bank_name = models.CharField(max_length=255)
#     address = models.CharField(max_length=225, default='Unknown', null=True, blank=True)
#     amount = models.DecimalField(max_digits=20, decimal_places=2)
#     timestamp = models.DateTimeField(default=timezone.now)
#     method = models.CharField(max_length=100, default='Manual')  # e.g., Card, Admin, Bank, etc.
#     reference = models.CharField(max_length=255, blank=True, null=True)
#     note = models.TextField(blank=True, null=True)

#     def __str__(self):
#         return f"{self.user.username} deposited {self.amount}"



class Deposit(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='deposits')
    bank_name = models.CharField(max_length=255)
    address = models.CharField(max_length=225, default='Unknown', null=True, blank=True)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    timestamp = models.DateTimeField(default=timezone.now)
    method = models.CharField(max_length=100, default='Manual')  # e.g., Card, Admin, Bank, etc.
    reference = models.CharField(max_length=255, blank=True, null=True)
    note = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        is_new = self._state.adding  # Check if new deposit

        super().save(*args, **kwargs)  # Save deposit first

        if is_new:
            account = self.user.account
            account.balance += self.amount
            account.save()
