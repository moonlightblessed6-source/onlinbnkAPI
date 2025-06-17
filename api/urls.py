from django.urls import path
from .views import *
from rest_framework.authtoken.views import obtain_auth_token



urlpatterns = [
    path('account/dashboard', AccountAPIView.as_view(), name = 'dashboard'),
    path('api/login/', obtain_auth_token, name='api_token_auth'),
    path('login/', LoginView.as_view(), name ='account'),
    # path('logout', LogoutView.as_view(), name = 'logout'),
    path('transfers/', TransferAPIView.as_view(), name='transfer-create'),
    path('transfers/<int:transfer_id>/verify/', TransferVerifyAPIView.as_view(), name='transfer-verify'),
    # path('transfers/history/', TransferHistoryAPIView.as_view(), name='transfer-history'),
    path('transactions/history/', TransactionHistoryView.as_view(), name='transaction-history'),
    # path('deposithistory/', DepositCreateAPIView.as_view(), name='deposits')
]
