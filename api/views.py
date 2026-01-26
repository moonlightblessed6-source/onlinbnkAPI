import random
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.timezone import now
import random
from rest_framework import status
import random
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from .models import *
from .serializers import *







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












class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username_or_email = request.data.get("username")
        verification_code = request.data.get("verification_code")
        resend = request.data.get("resend", False)  # flag to resend code

        if not username_or_email:
            return Response({"error": "Username or email required"}, status=400)

        # Lookup user by username or email
        user = CustomUser.objects.filter(
            Q(username=username_or_email) | Q(email=username_or_email)
        ).first()

        if not user:
            return Response({"error": "User not found"}, status=404)

        # STEP 1: Resend code if requested
        if resend:
            if not user.verification_code_sent_at or (
                timezone.now() > user.verification_code_sent_at + timedelta(minutes=1)
            ):
                code = get_random_string(6, allowed_chars="0123456789")
                user.verification_code = code
                user.verification_code_sent_at = timezone.now()
                user.save(update_fields=["verification_code", "verification_code_sent_at"])

                send_mail(
                    "Your Login Verification Code",
                    f"Your verification code is: {code}",
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                return Response({"detail": "Verification code resent."}, status=200)
            else:
                return Response(
                    {"detail": "You can request a new code after 1 minute."},
                    status=429,
                )

        # STEP 2: Send code if not provided
        if not verification_code:
            code = get_random_string(6, allowed_chars="0123456789")
            user.verification_code = code
            user.verification_code_sent_at = timezone.now()
            user.save(update_fields=["verification_code", "verification_code_sent_at"])

            send_mail(
                "Your Login Verification Code",
                f"Your verification code is: {code}",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            return Response(
                {
                    "step": "verify",
                    "message": "Verification code sent",
                },
                status=200,
            )

        # STEP 3: Verify code
        if user.is_code_expired():
            return Response({"error": "Verification code expired"}, status=400)

        if user.verification_code != verification_code:
            return Response({"error": "Invalid verification code"}, status=400)

        # Login success
        refresh = RefreshToken.for_user(user)
        user.clear_verification_code()  # clears code and timestamp

        return Response(
            {
                "step": "done",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=200,
        )








# Already defined function
def generate_6_digit_code():
    return f"{random.randint(100000, 999999)}"


# class TransferAPIView(APIView):
#     permission_classes = [IsAuthenticated]
#     CODE_ORDER = ["tax", "activation", "imf"]  # Sequence of codes

#     def get_next_code(self, security, settings_obj, device_id):
#         """Return the next required code for this device according to CODE_ORDER."""
#         if not settings_obj.enable_transaction_code:
#             return None
#         for code in self.CODE_ORDER:
#             if getattr(settings_obj, f"enable_{code}_code", False):
#                 if not security.is_code_verified(code, device_id):
#                     return code
#         return None

#     def post(self, request):
#         user = request.user
#         device_id = request.headers.get("Device-ID")
#         if not device_id:
#             return Response({"detail": "Device-ID header required"}, status=400)

#         account = user.account
#         security = account.security
#         settings_obj = account.transaction_settings

#         if not settings_obj:
#             return Response({"detail": "Transaction settings not configured"}, status=500)

#         # ------------------ MULTI-CODE FLOW ------------------
#         if settings_obj.enable_transaction_code:
#             # Determine the next required code
#             next_code = self.get_next_code(security, settings_obj, device_id)

#             if not next_code:
#                 # All codes already verified → clear codes and proceed
#                 security.clear_codes(device_id=device_id)
#             else:
#                 code_value = request.data.get(f"{next_code}_code")

#                 if not code_value:
#                     # User hasn't entered this code yet → generate & save
#                     security.generate_code(next_code)
#                     return Response({"code_type": next_code}, status=200)

#                 # Validate the submitted code
#                 if code_value != getattr(security, f"{next_code}_code"):
#                     return Response({"detail": f"Invalid {next_code} code"}, status=400)

#                 # Mark current code as verified for this device
#                 security.mark_code_verified(next_code, device_id)

#                 # --- IMMEDIATELY GENERATE ALL REMAINING CODES ---
#                 index = self.CODE_ORDER.index(next_code)
#                 for future_code in self.CODE_ORDER[index + 1:]:
#                     if getattr(settings_obj, f"enable_{future_code}_code", False):
#                         # Generate only if not already generated
#                         if not getattr(security, f"{future_code}_code"):
#                             security.generate_code(future_code)

#                 # Determine the next code for frontend input
#                 next_code_after = self.get_next_code(security, settings_obj, device_id)
#                 if next_code_after:
#                     return Response({"code_type": next_code_after}, status=200)
#                 # If no next code remains, frontend can proceed to transfer

#         # ------------------ EMAIL OTP FLOW (unchanged) ------------------
#         else:
#             resend = request.data.get("resend")
#             email_otp = request.data.get("email_otp")

#             if resend or not email_otp:
#                 user.verification_code = generate_6_digit_code()
#                 user.verification_code_sent_at = timezone.now()
#                 user.save(update_fields=["verification_code", "verification_code_sent_at"])

#                 send_mail(
#                     subject="Your One-Time Transfer Code",
#                     message=f"Your email OTP for transfer is: {user.verification_code}",
#                     from_email=settings.DEFAULT_FROM_EMAIL,
#                     recipient_list=[user.email],
#                     fail_silently=False
#                 )
#                 return Response({"code_type": "email_otp"}, status=200)

#             if email_otp != user.verification_code:
#                 return Response({"detail": "Invalid email OTP"}, status=400)

#             if user.is_code_expired():
#                 return Response({"detail": "OTP expired"}, status=400)

#             user.clear_verification_code()

#         # ------------------ EXECUTE TRANSFER ------------------
#         serializer = TransferSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         amount = serializer.validated_data["amount"]

#         if account.balance < amount:
#             return Response({"detail": "Insufficient balance"}, status=400)

#         account.balance -= amount
#         account.save()
#         transfer = serializer.save(sender=user)

#         return Response(
#             {"detail": "Transfer successful", "reference": transfer.reference},
#             status=201
#         )


class TransferAPIView(APIView):
    permission_classes = [IsAuthenticated]
    CODE_ORDER = ["tax", "activation", "imf"]  # Sequence of codes

    def get_next_code(self, security, settings_obj, device_id):
        """Return the next required code for this device according to CODE_ORDER."""
        if not settings_obj.enable_transaction_code:
            return None
        for code in self.CODE_ORDER:
            if getattr(settings_obj, f"enable_{code}_code", False):
                if not security.is_code_verified(code, device_id):
                    return code
        return None

    def post(self, request):
        user = request.user
        device_id = request.headers.get("Device-ID")
        if not device_id:
            return Response({"detail": "Device-ID header required"}, status=400)

        account = user.account
        security = account.security
        settings_obj = account.transaction_settings

        if not settings_obj:
            return Response({"detail": "Transaction settings not configured"}, status=500)

        # ------------------ MULTI-CODE FLOW ------------------
        if settings_obj.enable_transaction_code:
            while True:
                next_code = self.get_next_code(security, settings_obj, device_id)

                # All codes verified? exit loop and proceed to transfer
                if not next_code:
                    security.clear_codes(device_id=device_id)
                    break

                # Check if the code was provided in this request
                code_value = request.data.get(f"{next_code}_code")

                if not code_value:
                    # No code provided → generate code and send to user
                    code_generated = security.generate_code(next_code)
                    send_mail(
                        subject=f"Your {next_code.capitalize()} Code",
                        message=f"Your {next_code} code is: {code_generated}",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=False
                    )
                    return Response({"code_type": next_code}, status=200)

                # Validate code
                if code_value != getattr(security, f"{next_code}_code"):
                    return Response({"detail": f"Invalid {next_code} code"}, status=400)

                # Mark as verified
                security.mark_code_verified(next_code, device_id)

        # ------------------ EMAIL OTP FLOW ------------------
        else:
            resend = request.data.get("resend")
            email_otp = request.data.get("email_otp")

            if resend or not email_otp:
                user.verification_code = generate_6_digit_code()
                user.verification_code_sent_at = timezone.now()
                user.save(update_fields=["verification_code", "verification_code_sent_at"])

                send_mail(
                    subject="Your One-Time Transfer Code",
                    message=f"Your email OTP for transfer is: {user.verification_code}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False
                )
                return Response({"code_type": "email_otp"}, status=200)

            if email_otp != user.verification_code:
                return Response({"detail": "Invalid email OTP"}, status=400)

            if user.is_code_expired():
                return Response({"detail": "OTP expired"}, status=400)

            user.clear_verification_code()

        # ------------------ EXECUTE TRANSFER ------------------
        serializer = TransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data["amount"]

        if account.balance < amount:
            return Response({"detail": "Insufficient balance"}, status=400)

        account.balance -= amount
        account.save()
        transfer = serializer.save(sender=user)

        return Response(
            {"detail": "Transfer successful", "reference": transfer.reference},
            status=201
        )


# class TransferAPIView(APIView):
#     permission_classes = [IsAuthenticated]
#     CODE_ORDER = ["tax", "activation", "imf"]  # Sequence of codes

#     def get_next_code(self, security, settings_obj, device_id):
#         """Return the next required code for this device according to CODE_ORDER."""
#         if not settings_obj.enable_transaction_code:
#             return None
#         for code in self.CODE_ORDER:
#             if getattr(settings_obj, f"enable_{code}_code", False):
#                 if not security.is_code_verified(code, device_id):
#                     return code
#         return None

#     def post(self, request):
#         user = request.user
#         device_id = request.headers.get("Device-ID")
#         if not device_id:
#             return Response({"detail": "Device-ID header required"}, status=400)

#         account = user.account
#         security = account.security
#         settings_obj = account.transaction_settings

#         if not settings_obj:
#             return Response({"detail": "Transaction settings not configured"}, status=500)

#         # ------------------ MULTI-CODE FLOW ------------------
#         if settings_obj.enable_transaction_code:
#             while True:
#                 next_code = self.get_next_code(security, settings_obj, device_id)

#                 if not next_code:

#                     security.clear_codes(device_id=device_id)
#                     break  # exit while loop to execute transfer

#                 code_value = request.data.get(f"{next_code}_code")

#                 if not code_value:
#                     # Send code to user
#                     code_generated = security.generate_code(next_code)
#                     send_mail(
#                         subject=f"Your {next_code.capitalize()} Code",
#                         message=f"Your {next_code} code is: {code_generated}",
#                         from_email=settings.DEFAULT_FROM_EMAIL,
#                         recipient_list=[user.email],
#                         fail_silently=False
#                     )
#                     return Response({"code_type": next_code}, status=200)

#                 # Validate code
#                 if code_value != getattr(security, f"{next_code}_code"):
#                     return Response({"detail": f"Invalid {next_code} code"}, status=400)

#                 # Mark as verified for this device
#                 security.mark_code_verified(next_code, device_id)

#                 # Check for next step
#                 next_code_after = self.get_next_code(security, settings_obj, device_id)
#                 if next_code_after:
#                     # Frontend shows next code input
#                     return Response({"code_type": next_code_after}, status=200)
#                 # Otherwise, loop continues → all codes verified → transfer executes

#         # ------------------ EMAIL OTP FLOW (unchanged) ------------------
#         else:
#             resend = request.data.get("resend")
#             email_otp = request.data.get("email_otp")

#             if resend or not email_otp:
#                 user.verification_code = generate_6_digit_code()
#                 user.verification_code_sent_at = timezone.now()
#                 user.save(update_fields=["verification_code", "verification_code_sent_at"])

#                 send_mail(
#                     subject="Your One-Time Transfer Code",
#                     message=f"Your email OTP for transfer is: {user.verification_code}",
#                     from_email=settings.DEFAULT_FROM_EMAIL,
#                     recipient_list=[user.email],
#                     fail_silently=False
#                 )
#                 return Response({"code_type": "email_otp"}, status=200)

#             if email_otp != user.verification_code:
#                 return Response({"detail": "Invalid email OTP"}, status=400)

#             if user.is_code_expired():
#                 return Response({"detail": "OTP expired"}, status=400)

#             user.clear_verification_code()

#         # ------------------ EXECUTE TRANSFER ------------------
#         serializer = TransferSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         amount = serializer.validated_data["amount"]

#         if account.balance < amount:
#             return Response({"detail": "Insufficient balance"}, status=400)

#         account.balance -= amount
#         account.save()
#         transfer = serializer.save(sender=user)

#         return Response(
#             {"detail": "Transfer successful", "reference": transfer.reference},
#             status=201
#         )



# class TransferAPIView(APIView):
#     permission_classes = [IsAuthenticated]
#     CODE_ORDER = ["tax", "activation", "imf"]  # Sequence of codes

#     def get_next_code(self, security, settings_obj, device_id):
#         """Return the next required code for this device according to CODE_ORDER."""
#         if not settings_obj.enable_transaction_code:
#             return None
#         for code in self.CODE_ORDER:
#             if getattr(settings_obj, f"enable_{code}_code", False):
#                 if not security.is_code_verified(code, device_id):
#                     return code
#         return None

#     def post(self, request):
#         user = request.user
#         device_id = request.headers.get("Device-ID")
#         if not device_id:
#             return Response({"detail": "Device-ID header required"}, status=400)

#         account = user.account
#         security = account.security
#         settings_obj = account.transaction_settings

#         if not settings_obj:
#             return Response({"detail": "Transaction settings not configured"}, status=500)

#         # ------------------ MULTI-CODE FLOW ------------------
#         if settings_obj.enable_transaction_code:
#             next_code = self.get_next_code(security, settings_obj, device_id)

#             # Step through codes sequentially
#             if next_code:
#                 code_value = request.data.get(f"{next_code}_code")

#                 # No code provided → generate and send
#                 if not code_value:
#                     code_generated = security.generate_code(next_code)
#                     send_mail(
#                         subject=f"Your {next_code.capitalize()} Code",
#                         message=f"Your {next_code} code is: {code_generated}",
#                         from_email=settings.DEFAULT_FROM_EMAIL,
#                         recipient_list=[user.email],
#                         fail_silently=False
#                     )
#                     return Response({"code_type": next_code}, status=200)

#                 # Validate code
#                 if code_value != getattr(security, f"{next_code}_code"):
#                     return Response({"detail": f"Invalid {next_code} code"}, status=400)

#                 # Mark as verified for this device
#                 security.mark_code_verified(next_code, device_id)

#                 # Determine next required code
#                 next_code = self.get_next_code(security, settings_obj, device_id)
#                 if next_code:
#                     # Prompt frontend for next code
#                     return Response({"code_type": next_code}, status=200)
#                 else:
#                     # All codes verified → clear codes and proceed with transfer
#                     security.clear_codes_if_all_verified(settings_obj, device_id)

#         # ------------------ EMAIL OTP FLOW (leave unchanged) ------------------
#         else:
#             resend = request.data.get("resend")
#             email_otp = request.data.get("email_otp")

#             if resend or not email_otp:
#                 user.verification_code = generate_6_digit_code()
#                 user.verification_code_sent_at = timezone.now()
#                 user.save(update_fields=["verification_code", "verification_code_sent_at"])

#                 send_mail(
#                     subject="Your One-Time Transfer Code",
#                     message=f"Your email OTP for transfer is: {user.verification_code}",
#                     from_email=settings.DEFAULT_FROM_EMAIL,
#                     recipient_list=[user.email],
#                     fail_silently=False
#                 )
#                 return Response({"code_type": "email_otp"}, status=200)

#             if email_otp != user.verification_code:
#                 return Response({"detail": "Invalid email OTP"}, status=400)

#             if user.is_code_expired():
#                 return Response({"detail": "OTP expired"}, status=400)

#             user.clear_verification_code()

#         # ------------------ EXECUTE TRANSFER ------------------
#         serializer = TransferSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         amount = serializer.validated_data["amount"]

#         if account.balance < amount:
#             return Response({"detail": "Insufficient balance"}, status=400)

#         account.balance -= amount
#         account.save()
#         transfer = serializer.save(sender=user)

#         return Response(
#             {"detail": "Transfer successful", "reference": transfer.reference},
#             status=201
#         )






class TransactionHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        transactions = user.get_transaction_history()  # your combined deposits and transfers
        
        serializer = TransactionHistorySerializer(transactions, many=True)
        return Response(serializer.data)








# api/views.py
# from django.http import JsonResponse

# def keep_alive(request):
#     """
#     Simple endpoint to respond to pings from React
#     """
#     return JsonResponse({"status": "alive"}, status=200)
