from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Account, Transfer, Deposit

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # Add the new transfer lock field
    fieldsets = UserAdmin.fieldsets + (
        ('Security Settings', {'fields': ('is_locked', 'is_transfer_locked')}),
    )

    # Show email, login lock, and transfer lock in list view
    list_display = UserAdmin.list_display + ('email', 'is_locked', 'is_transfer_locked')
    list_filter = UserAdmin.list_filter + ('is_locked', 'is_transfer_locked')
    
    # Add admin actions
    actions = ['lock_users', 'unlock_users', 'lock_transfers', 'unlock_transfers']

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
    lock_transfers.short_description = "Lock transfers for selected users"

    def unlock_transfers(self, request, queryset):
        updated = queryset.update(is_transfer_locked=False)
        self.message_user(request, f"{updated} user(s) transfer unlocked.")
    unlock_transfers.short_description = "Unlock transfers for selected users"

# Keep the rest of your admin registrations
@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'first_name', 'last_name', 'phone', 'nationality', 'gender', 'street', 'apt_suite', 'city', 'state', 'zip_code', 'balance', 'account_number')
    search_fields = ('first_name', 'last_name', 'phone', 'user__username')


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'amount', 'recipient_address', 'status', 'timestamp')
    list_filter = ('status', 'timestamp')
    search_fields = ('sender__username', 'receiver__username')


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)
        if is_new:
            account = obj.user.account
            account.balance += obj.amount
            account.save()
