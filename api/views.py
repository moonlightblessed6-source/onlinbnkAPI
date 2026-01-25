import random
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.utils.timezone import now
from django.utils.crypto import get_random_string
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from .models import *
from .serializers import *






class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username_or_email = request.data.get("username")
        verification_code = request.data.get("verification_code")

        if not username_or_email:
            return Response({"error": "Username or email required"}, status=400)

        user = User.objects.filter(
            Q(username=username_or_email) | Q(email=username_or_email)
        ).first()

        if not user:
            return Response({"error": "User not found"}, status=404)

        # STEP 1: Send code
        if not verification_code:
            code = get_random_string(6, allowed_chars="0123456789")
            user.verification_code = code
            user.verification_code_sent_at = timezone.now()
            user.verification_code_expired = False
            user.save()

            send_mail(
                "Your Login Verification Code",
                f"Your verification code is: {code}",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            return Response({
                "step": "verify",
                "message": "Verification code sent"
            }, status=200)

        # STEP 2: Verify code
        if user.verification_code != verification_code:
            return Response({"error": "Invalid verification code"}, status=400)

        if not user.verification_code_sent_at or (
            timezone.now() > user.verification_code_sent_at + timedelta(minutes=5)
        ):
            return Response({"error": "Verification code expired"}, status=400)

        # STEP 3: Login success
        refresh = RefreshToken.for_user(user)

        user.verification_code = None
        user.verification_code_sent_at = None
        user.verification_code_expired = False
        user.save()

        return Response({
            "step": "done",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }, status=200)


class AccountAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        account, created = Account.objects.get_or_create(
            user=user,
            defaults={
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }
        )

        account_data = {
            "username": user.username,
            "first_name": account.first_name,
            "last_name": account.last_name,
            "email": account.email,
            "phone": account.phone,
            "nationality": account.nationality,
            "gender": account.gender,
            "street": account.street,
            "apt_suite": account.apt_suite,
            "city": account.city,
            "state": account.state,
            "zip_code": account.zip_code,
            "balance": account.balance,
            "account_number": account.account_number,
            "avatar_url": account.avatar.url if account.avatar else None,
            "date_created": account.date_created.strftime('%Y-%m-%d %H:%M:%S'),
        }

        return Response({
            "message": "Dashboard loaded successfully",
            "account": account_data,
            "current_time": now().isoformat(),
        }, status=200)




# class LoginView(APIView):
#     permission_classes = [AllowAny]

#     def post(self, request):
#         # Make sure request.data is used correctly
#         username_or_email = request.data.get("username")
#         password = request.data.get("password")

#         if not username_or_email or not password:
#             return Response({"error": "Username/email and password required"}, status=status.HTTP_400_BAD_REQUEST)

#         # Find user by username or email
#         user_obj = User.objects.filter(Q(username=username_or_email) | Q(email=username_or_email)).first()
#         if not user_obj:
#             return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

#         # Authenticate user
#         user = authenticate(username=user_obj.username, password=password)
#         if not user:
#             return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

#         # Generate JWT
#         refresh = RefreshToken.for_user(user)

#         return Response({
#             "access": str(refresh.access_token),
#             "refresh": str(refresh),
#             "user_id": user.id,
#             "username": user.username
#         }, status=status.HTTP_200_OK)




     

class TransferAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # Check if transfer is locked
        if user.is_transfer_locked:
            return Response({
                'detail': 'Your account is currently restricted from sending money. Please contact support.'
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            serializer = TransferSerializer(data=request.data, context={'request': request})
            
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            amount = serializer.validated_data['amount']
            sender_account = user.account

            if sender_account.balance < amount:
                return Response({'detail': 'Insufficient balance.'}, status=status.HTTP_400_BAD_REQUEST)

            code = str(random.randint(100000, 999999))

            transfer = serializer.save(
                sender=user,
                verification_code=code,
                status='P',
                is_verified=False,
                receiver_name=serializer.validated_data.get('receiver_name'),
                receiver_account=serializer.validated_data.get('receiver_account'),
                receiver_bank=serializer.validated_data.get('receiver_bank'),
                )


            send_mail(
                subject='Your Transfer Verification Code',
                message=f'Your verification code is: {code}',
                from_email='support@eloanhub.com',
                recipient_list=[user.email],
                fail_silently=False,
            )

            return Response({
                'detail': 'Transfer created. Verification code sent.',
                'transfer_id': transfer.id
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'detail': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




# class TransferVerifyAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     @transaction.atomic
#     def post(self, request, transfer_id):
#         try:
#             transfer = Transfer.objects.select_for_update().get(pk=transfer_id)
#         except Transfer.DoesNotExist:
#             return Response({'detail': 'Transfer not found.'}, status=404)

#         if transfer.sender != request.user:
#             return Response({'detail': 'Unauthorized.'}, status=403)

#         if transfer.is_verified:
#             return Response({'detail': 'Transfer already verified.'}, status=400)

#         code = request.data.get('verification_code')
#         if code != transfer.verification_code:
#             return Response({'detail': 'Invalid verification code.'}, status=400)

#         if request.user.account.balance < transfer.amount:
#             transfer.status = 'F'
#             transfer.code_entered = True
#             transfer.save(update_fields=['status', 'code_entered'])
#             return Response({'detail': 'Insufficient balance.'}, status=400)

#         transfer.is_verified = True
#         transfer.code_entered = True
#         transfer.status = 'P'
#         transfer.save(update_fields=['is_verified', 'status', 'code_entered'])

#         return Response(
#             {'detail': 'Transfer verified. Awaiting admin approval.'},
#             status=200
#         )


class TransferVerifyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, transfer_id):
        try:
            transfer = Transfer.objects.select_for_update().get(pk=transfer_id)
        except Transfer.DoesNotExist:
            return Response({'detail': 'Transfer not found.'}, status=404)

        if transfer.sender != request.user:
            return Response({'detail': 'Unauthorized.'}, status=403)

        if transfer.is_verified:
            return Response({'detail': 'Transfer already verified.'}, status=400)

        code = request.data.get('verification_code')
        if not code or code != transfer.verification_code:
            return Response({'detail': 'Invalid verification code.'}, status=400)

        if transfer.sender.account.balance < transfer.amount:
            transfer.status = 'F'
            transfer.code_entered = True
            transfer.save(update_fields=['status', 'code_entered'])
            return Response({'detail': 'Insufficient balance.'}, status=400)

        transfer.is_verified = True
        transfer.code_entered = True
        transfer.status = 'P'
        transfer.save(update_fields=['is_verified', 'status', 'code_entered'])

        return Response(
            {'detail': 'Transfer verified. Awaiting admin approval.'},
            status=200
        )




class TransactionHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        transactions = user.get_transaction_history()  # your combined deposits and transfers
        
        serializer = TransactionHistorySerializer(transactions, many=True)
        return Response(serializer.data)





# api/views.py
from django.http import JsonResponse

def keep_alive(request):
    """
    Simple endpoint to respond to pings from React
    """
    return JsonResponse({"status": "alive"}, status=200)
