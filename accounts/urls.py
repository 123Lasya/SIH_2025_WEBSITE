from django.urls import path
from . import views

urlpatterns = [
    path('select-role/', views.select_role, name='select_role'),

    # ---------------- FARMER SIGNUP ----------------
    path('farmer/aadhaar/', views.farmer_aadhaar, name='farmer_aadhaar'),
    path('farmer/otp/', views.farmer_otp, name='farmer_otp'),
    path('farmer/register/', views.farmer_register, name='farmer_register'),
    path('farmer/bank/', views.farmer_bank, name='farmer_bank'),
 
    # ---------------- WALLET (FINAL) ----------------
    path("wallet/add/", views.wallet_add, name="wallet_add"),
    path("wallet/add/success/", views.wallet_add_success, name="wallet_add_success"),

    # ---------------- BUYER SIGNUP ----------------
    path('buyer/email/', views.buyer_email, name='buyer_email'),
    path('buyer/otp/', views.buyer_otp, name='buyer_otp'),
    path('buyer/type/', views.buyer_type, name='buyer_type'),
    path('buyer/business/', views.buyer_business, name='buyer_business'),
    path('buyer/trader/', views.buyer_trader, name='buyer_trader'),
    path('buyer/bank/', views.buyer_bank, name='buyer_bank'),

    # ---------------- REGISTRATION DONE ----------------
    path('register/success/', views.register_success, name='register_success'),

    # ---------------- LOGIN / LOGOUT ----------------
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
