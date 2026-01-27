from django.urls import path
from .views import (
    AccountAPIView,
    LoginView,
    TransferAPIView,
    TransactionHistoryView,
    SaveRegistrationAPIView,  # <-- make sure this is imported
)

urlpatterns = [
    path("account/dashboard", AccountAPIView.as_view(), name="dashboard"),
    #  path('keep-alive/', keep_alive, name='keep-alive'),
    path("login/", LoginView.as_view(), name="account"),
    path("transfers/", TransferAPIView.as_view(), name="transfer-create"),
    path(
        "transactions/history/",
        TransactionHistoryView.as_view(),
        name="transaction-history",
    ),
    path('save/', SaveRegistrationAPIView.as_view(), name='save-registration'),
]
