from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db import transaction

from .models import (
    CustomUser,
    Account,
    Transfer,
    Deposit,
    TransactionSettings,
    AccountSecurity,
    Register,
)


admin.site.register(Register)

# ===================== USERS =====================
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Security Settings", {"fields": ("is_locked", "is_transfer_locked")}),
    )

    list_display = UserAdmin.list_display + (
        "email",
        "is_locked",
        "is_transfer_locked",
    )

    list_filter = UserAdmin.list_filter + (
        "is_locked",
        "is_transfer_locked",
    )

    actions = [
        "lock_users",
        "unlock_users",
        "lock_transfers",
        "unlock_transfers",
    ]

    def lock_users(self, request, queryset):
        updated = queryset.update(is_locked=True)
        self.message_user(request, f"{updated} user(s) locked.")

    lock_users.short_description = "Lock selected users"

    def unlock_users(self, request, queryset):
        updated = queryset.update(is_locked=False)
        self.message_user(request, f"{updated} user(s) unlocked.")

    unlock_users.short_description = "Unlock selected users"

    def lock_transfers(self, request, queryset):
        updated = queryset.update(is_transfer_locked=True)
        self.message_user(request, f"{updated} user(s) transfer locked.")

    lock_transfers.short_description = "Lock transfers"

    def unlock_transfers(self, request, queryset):
        updated = queryset.update(is_transfer_locked=False)
        self.message_user(request, f"{updated} user(s) transfer unlocked.")

    unlock_transfers.short_description = "Unlock transfers"


# ===================== ACCOUNTS =====================
@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "first_name",
        "last_name",
        "phone",
        "nationality",
        "gender",
        "balance",
        "account_number",
    )
    search_fields = (
        "first_name",
        "last_name",
        "phone",
        "user__username",
        "account_number",
    )


# ===================== TRANSFERS =====================
# ===================== TRANSFERS =====================
@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "sender",
        "receiver_account",
        "receiver_bank",
        "iban",  # ✅ added
        "swift_code",  # ✅ added
        "amount",
        "status",
        "timestamp",
    )

    list_filter = ("status", "receiver_bank")
    search_fields = ("reference", "receiver_account", "sender__username")

    actions = ["approve_transfer", "decline_transfer"]

    @transaction.atomic
    def approve_transfer(self, request, queryset):
        queryset.filter(status="P").update(status="S")

    @transaction.atomic
    def decline_transfer(self, request, queryset):
        for transfer in queryset.filter(status="P"):
            sender_account = transfer.sender.account
            sender_account.balance += transfer.amount
            sender_account.save()
            transfer.status = "F"
            transfer.save()




@admin.register(TransactionSettings)
class TransactionSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "updated_at",
        "enable_transaction_code",
        "enable_activation_code",
        "enable_tax_code",
        "enable_imf_code",
    )
    list_editable = ("enable_transaction_code",)
    list_display_links = ("updated_at",)  # Must set a link that's not editable


# ===================== DEPOSITS =====================
@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ("user", "bank_name", "amount", "timestamp", "reference")

    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)

        if is_new:
            account = obj.user.account
            account.balance += obj.amount
            account.save()


# ===================== ACCOUNT SECURITY =====================
@admin.register(AccountSecurity)
class AccountSecurityAdmin(admin.ModelAdmin):
    list_display = (
        "account",
        "activation_code",
        "tax_code",
        "imf_code",
        "updated_at",
    )
    readonly_fields = (
        "activation_code",
        "tax_code",
        "imf_code",
        "updated_at",
    )
