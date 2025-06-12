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
            'phone', 'email', 'nationality', 'gender', 'balance',
            'date_created', 'avatar'
        ]
        read_only_fields = ['date_created']


# Transfer Serializer




class TransferSerializer(serializers.ModelSerializer):
    sender = serializers.HiddenField(default=serializers.CurrentUserDefault())
    receiver = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True)
    external_receiver_email = serializers.EmailField(required=False, allow_null=True)
    external_receiver_name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Transfer
        fields = [
            'id', 'sender', 'receiver', 'external_receiver_email', 'external_receiver_name', 'amount', 'account', 'bank_name', 'address', 'amount',
            'timestamp', 'status', 'note', 'is_verified'
        ]
        read_only_fields = ['timestamp', 'status', 'is_verified']

    def validate(self, data):
        if not data.get('receiver') and not data.get('external_receiver_email'):
            raise serializers.ValidationError("You must provide either an internal receiver or an external receiver email.")
        return data







class DepositSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deposit
        fields = ['id', 'bank_name', 'address', 'amount', 'timestamp', 'method', 'reference', 'note']
