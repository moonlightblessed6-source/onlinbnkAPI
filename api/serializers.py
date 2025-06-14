from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import *
import datetime

User = get_user_model()


class AdminUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'is_locked', 'is_staff', 'is_superuser']

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
        ]
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value








class DepositSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deposit
        fields = ['id', 'bank_name', 'address', 'amount', 'timestamp', 'method', 'reference', 'note']
