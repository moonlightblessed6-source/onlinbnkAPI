from django.urls import path
from .views import *

urlpatterns = [
    path('login/', LoginAPIView.as_view(), name ='account'),
    path('transfers/', TransferAPIView.as_view(), name='transfer-create'),
    path('transfers/<int:transfer_id>/verify/', TransferVerifyAPIView.as_view(), name='transfer-verify'),
    path('transfers/history/', TransferHistoryAPIView.as_view(), name='transfer-history'),
    path('deposithistory/', DepositCreateAPIView.as_view(), name='deposits')
]
