from django.contrib.auth import authenticate
from django.db import transaction
from django.utils.timezone import now
from django.db.models import Q
import traceback
from django.core.mail import send_mail
from .models import Transfer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
# from rest_framework.exceptions import ValidationError, AuthenticationFailed
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from api.models import Transfer

import random

from .models import *
from .models import Deposit
from .serializers import *
from .serializers import DepositSerializer



class AccountAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            account = Account.objects.get(user=user)

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

            current_time = now().isoformat()

            return Response({
                "message": "Dashboard loaded successfully",
                "account": account_data,
                "current_time": current_time,
            }, status=status.HTTP_200_OK)

        except Account.DoesNotExist:
            return Response({"error": "Account not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        login_input = request.data.get('username', '').strip()
        password = request.data.get('password', '')

        if not login_input or not password:
            return Response({"error": "Please provide username/email and password."},
                            status=status.HTTP_400_BAD_REQUEST)

        user_obj = User.objects.filter(Q(username=login_input) | Q(email=login_input)).first()
        if not user_obj:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if getattr(user_obj, 'is_locked', False):
            return Response({"error": "Dear Customer, we have discovered suspicious activities on your account. An unauthorized IP address attempted to carry out a transaction on your account and credit card. Consequently, your account has been flagged by our risk assessment department. Kindly visit our nearest branch to confirm your identity before it can be reactivated. For more information, kindly contact our online customer care representative at info@fcujetscreem.org."}, status=status.HTTP_403_FORBIDDEN)

        user = authenticate(username=user_obj.username, password=password)
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                "message": "User logged in successfully!",
                "token": token.key,
                "user_id": user.id,
                "username": user.username,
            })
        return Response({"error": "Invalid username/email or password."}, status=status.HTTP_401_UNAUTHORIZED)


# class LogoutView(APIView):
#     permission_classes = [AllowAny]

#     def post(self, request):
#         try:
#             logout(request)
#             return Response({"message": "User logged out successfully!"}, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)










class TransferAPIView(APIView):
    permission_classes = [IsAuthenticated]
    # permission_classes = [AllowAny]

    def post(self, request):
        try:
            serializer = TransferSerializer(data=request.data, context={'request': request})
            
            if not serializer.is_valid():
                print("❌ Validation Errors:", serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            amount = serializer.validated_data['amount']
            sender_account = request.user.account

            if sender_account.balance < amount:
                return Response({'detail': 'Insufficient balance.'}, status=status.HTTP_400_BAD_REQUEST)

            code = str(random.randint(100000, 999999))

            transfer = serializer.save(
                sender=request.user,
                verification_code=code,
                status='P',  # Pending
                is_verified=False
            )

            # Send code to user email
            send_mail(
                subject='Your Transfer Verification Code',
                message=f'Your verification code is: {code}',
                from_email='moonlightblessed6@gmail.com',
                recipient_list=[request.user.email],
                fail_silently=False,
            )

            return Response({
                'detail': 'Transfer created. Verification code sent.',
                'transfer_id': transfer.id
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            print("💥 Transfer Error:", str(e))
            traceback.print_exc()
            return Response({'detail': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

# from django.core.mail import send_mail
# import logging

# logger = logging.getLogger(__name__)

# class TransferAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         try:
#             serializer = TransferSerializer(data=request.data, context={'request': request})
            
#             if not serializer.is_valid():
#                 print("❌ Validation Errors:", serializer.errors)
#                 return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
#             amount = serializer.validated_data['amount']
#             sender_account = request.user.account

#             if sender_account.balance < amount:
#                 return Response({'detail': 'Insufficient balance.'}, status=status.HTTP_400_BAD_REQUEST)

#             code = str(random.randint(100000, 999999))

#             transfer = serializer.save(
#                 sender=request.user,
#                 verification_code=code,
#                 status='P',  # Pending
#                 is_verified=False
#             )

#             # ✅ Debug print/log before email
#             print(f"📧 Sending code to {request.user.email}, code: {code}")
#             logger.debug(f"📧 Sending verification code {code} to {request.user.email}")

#             # Send email
#             send_mail(
#                 subject='Your Transfer Verification Code',
#                 message=f'Your verification code is: {code}',
#                 from_email='moonlightblessed6@gmail.com',
#                 recipient_list=[request.user.username],
#                 fail_silently=False,
#             )

#             print("✅ Email sent.")
#             logger.debug("✅ Email sent successfully.")

#             return Response({
#                 'detail': 'Transfer created. Verification code sent.',
#                 'transfer_id': transfer.id
#             }, status=status.HTTP_201_CREATED)

#         except Exception as e:
#             print("💥 Transfer Error:", str(e))
#             traceback.print_exc()
#             return Response({'detail': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        



class TransferVerifyAPIView(APIView):
    # permission_classes = [AllowAny]
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








class TransactionHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        transactions = user.get_transaction_history()  # your combined deposits and transfers
        
        serializer = TransactionHistorySerializer(transactions, many=True)
        return Response(serializer.data)
