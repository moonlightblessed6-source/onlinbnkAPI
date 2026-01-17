from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import *
import datetime

User = get_user_model()


class AdminUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'is_locked', 'is_transfer_locked', 'is_staff', 'is_superuser']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            password=validated_data['password']
        )
        user.is_locked = validated_data.get('is_locked', False)
        user.is_staff = validated_data.get('is_staff', False)
        user.is_superuser = validated_data.get('is_superuser', False)
        user.save()
        return user



# Custom User Serializer (limited for security)
class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_locked', 'is_active']


# Account Serializer
class AccountSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)

    class Meta:
        model = Account
        fields = [
            'id', 'user', 'first_name', 'last_name',
            'phone', 'email', 'nationality', 'gender', 'balance','street', 'apt_suite', 'city', 'state', 'zip_code', 'account_number',
            'date_created', 'avatar'
        ]
        read_only_fields = ['date_created', 'account_number']



# Transfer Serializer




class TransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transfer
        fields = [
            'receiver_account',
            'receiver_name',
            'receiver_bank',
            'swift_code',
            'purpose',
            'amount',
            'recipient_address',
            # 'iban',
            'nationality',
            'city',
            'zip_code',
            'state',
            'reference',
        ]
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value
    


class TransferVerificationSerializer(serializers.Serializer):
    verification_code = serializers.CharField(max_length=6)









class DepositSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deposit
        fields = ['id', 'bank_name', 'address', 'amount', 'timestamp', 'method', 'reference', 'purpose']







class TransactionHistorySerializer(serializers.Serializer):
    transaction_type = serializers.CharField()  # 'credit' or 'debit'
    amount = serializers.DecimalField(max_digits=20, decimal_places=2)
    timestamp = serializers.DateTimeField()
    description = serializers.CharField()
    reference = serializers.CharField(required=False, allow_blank=True)  # Only for deposit
    purpose = serializers.CharField(required=False, allow_blank=True)
    recipient_address = serializers.CharField(required=False, allow_blank=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Add extra details if needed
        if hasattr(instance, 'reference'):
            data['reference'] = instance.reference
        if hasattr(instance, 'purpose'):
            data['purpose'] = instance.purpose
        if hasattr(instance, 'recipient_address'):
            data['recipient_address'] = instance.recipient_address
        return data

