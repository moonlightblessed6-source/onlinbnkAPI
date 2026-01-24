from django.urls import path
from .views import *





urlpatterns = [
    path('account/dashboard', AccountAPIView.as_view(), name = 'dashboard'),
     path('keep-alive/', keep_alive, name='keep-alive'),
    path('login/', LoginView.as_view(), name ='account'),
    path('transfers/', TransferAPIView.as_view(), name='transfer-create'),
    path('transfers/<int:transfer_id>/verify/', TransferVerifyAPIView.as_view(), name='transfer-verify'),
    path('transactions/history/', TransactionHistoryView.as_view(), name='transaction-history'),

]
