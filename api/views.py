from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from django.core.mail import send_mail
import random
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from .models import *
from .serializers import *
from django.db import transaction
from rest_framework.generics import ListAPIView
from .models import Deposit
from .serializers import DepositSerializer




class AccountAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            account = request.user.account 
            serializer = AccountSerializer(account)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'errors': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class LoginAPIView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({'error': 'Please provide both username and password'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)

        if not user:
            raise AuthenticationFailed('Invalid credentials')

        if getattr(user, 'is_locked', False):
            return Response({'error': 'Your account is locked. Please contact support.'}, status=status.HTTP_403_FORBIDDEN)

        token, created = Token.objects.get_or_create(user=user)

        return Response({
            'token': token.key,
            'user_id': user.id,
            'username': user.username,
        }, status=status.HTTP_200_OK)




class TransferVerifyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, transfer_id):
        try:
            transfer = Transfer.objects.get(pk=transfer_id)
        except Transfer.DoesNotExist:
            return Response({'detail': 'Transfer not found.'}, status=status.HTTP_404_NOT_FOUND)

        if transfer.sender != request.user:
            return Response({'detail': 'Unauthorized.'}, status=status.HTTP_403_FORBIDDEN)

        if transfer.is_verified:
            return Response({'detail': 'Transfer already verified.'}, status=status.HTTP_400_BAD_REQUEST)

        code = request.data.get('code')
        if code != transfer.verification_code:
            return Response({'detail': 'Invalid verification code.'}, status=status.HTTP_400_BAD_REQUEST)

        sender_account = request.user.account

        if sender_account.balance < transfer.amount:
            transfer.status = 'F'
            transfer.save()
            return Response({'detail': 'Insufficient balance.'}, status=status.HTTP_400_BAD_REQUEST)

        # Deduct amount from sender
        sender_account.balance -= transfer.amount
        sender_account.save()

        # If internal receiver, credit amount
        if transfer.receiver:
            receiver_account = transfer.receiver.account
            receiver_account.balance += transfer.amount
            receiver_account.save()

        transfer.is_verified = True
        transfer.status = 'S'
        transfer.save()

        return Response({'detail': 'Transfer verified and completed.'}, status=status.HTTP_200_OK)




class TransferAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TransferSerializer(data=request.data)
        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            sender_account = request.user.account

            if sender_account.balance < amount:
                raise ValidationError("Insufficient balance to make this transfer.")

            # Generate verification code
            code = str(random.randint(100000, 999999))

            # Save transfer with code and status PENDING
            transfer = serializer.save(
                sender=request.user,
                verification_code=code,
                status='P',
                is_verified=False
            )

            # Send code via email
            send_mail(
                subject='Your Transfer Verification Code',
                message=f'Your verification code is: {code}',
                from_email='moonlightblessed6@gmail.com',
                recipient_list=[request.user.email],
                fail_silently=False,
            )

            return Response({
                'detail': 'Transfer created. Verification code sent to email.',
                'transfer_id': transfer.id
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    





class TransferHistoryAPIView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TransferSerializer

    def get_queryset(self):
        user = self.request.user
        return Transfer.objects.filter(
            models.Q(sender=user) | models.Q(receiver=user)
        ).order_by('-timestamp')







class DepositCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DepositSerializer(data=request.data)
        if serializer.is_valid():
            deposit = serializer.save(user=request.user)  # Create deposit
            
            # Update account balance
            account = request.user.account
            account.balance += deposit.amount
            account.save()

            return Response(DepositSerializer(deposit).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
