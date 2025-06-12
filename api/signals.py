

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.contrib.auth import logout
from django.contrib import messages
from django.shortcuts import redirect
from .models import Account

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_account(sender, instance, created, **kwargs):
    if created:
        # Check if any Account already uses this email
        if not Account.objects.filter(email=instance.email).exists():
            Account.objects.create(
                user=instance,
                email=instance.email,
                first_name=instance.first_name or '',
                last_name=instance.last_name or '',
            )
        else:
            # Optional: log this issue or handle it another way
            print(f"⚠️ Account with email {instance.email} already exists. Skipping creation.")

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_account(sender, instance, **kwargs):
    if hasattr(instance, 'account'):
        instance.account.save()

@receiver(user_logged_in)
def block_locked_users(sender, request, user, **kwargs):
    if getattr(user, 'is_locked', False):
        logout(request)
        messages.error(request, "Your account is locked. Please contact support.")
        return redirect('login')

