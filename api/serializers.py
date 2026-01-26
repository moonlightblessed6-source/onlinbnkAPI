from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import *

User = get_user_model()


# ===================== ADMIN USER CREATE =====================
class AdminUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "is_locked",
            "is_transfer_locked",
            "is_staff",
            "is_superuser",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")

        user = User.objects.create_user(password=password, **validated_data)
        return user


# ===================== USER (SAFE VIEW) =====================
class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "is_locked", "is_active"]


# ===================== ACCOUNT =====================
class AccountSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)

    class Meta:
        model = Account
        fields = [
            "id",
            "user",
            "first_name",
            "last_name",
            "phone",
            "email",
            "nationality",
            "gender",
            "balance",
            "street",
            "apt_suite",
            "city",
            "state",
            "zip_code",
            "account_number",
            "date_created",
            "avatar",
        ]
        read_only_fields = ["date_created", "account_number", "balance"]


# ===================== TRANSFER =====================
class TransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transfer
        fields = [
            "receiver_name",
            "receiver_bank",
            "receiver_account",
            "iban",  # ✅ included
            "swift_code",  # ✅ included
            "recipient_address",
            "purpose",
            "amount",
        ]


# ===================== DEPOSIT =====================
class DepositSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deposit
        fields = [
            "id",
            "bank_name",
            "address",
            "amount",
            "timestamp",
            "method",
            "reference",
            "purpose",
        ]


# ===================== TRANSACTION HISTORY =====================
class TransactionHistorySerializer(serializers.Serializer):
    transaction_type = serializers.CharField()
    amount = serializers.DecimalField(max_digits=20, decimal_places=2)
    timestamp = serializers.DateTimeField()
    description = serializers.CharField()
    reference = serializers.CharField(required=False, allow_null=True)
    purpose = serializers.CharField(required=False, allow_null=True)
    recipient_address = serializers.CharField(required=False, allow_null=True)

    receiver_name = serializers.SerializerMethodField()
    receiver_account = serializers.SerializerMethodField()
    receiver_bank = serializers.SerializerMethodField()

    def get_receiver_name(self, obj):
        if getattr(obj, "receiver_name", None):
            return obj.receiver_name
        if getattr(obj, "receiver", None):
            return f"{obj.receiver.first_name} {obj.receiver.last_name}"
        if getattr(obj, "bank_name", None):
            return obj.bank_name
        return None

    def get_receiver_account(self, obj):
        if getattr(obj, "receiver_account", None):
            return obj.receiver_account
        if getattr(obj, "receiver", None) and hasattr(obj.receiver, "account"):
            return obj.receiver.account.account_number
        return None

    def get_receiver_bank(self, obj):
        if getattr(obj, "receiver_bank", None):
            return obj.receiver_bank
        if getattr(obj, "bank_name", None):
            return obj.bank_name
        return "External Bank"
