from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import login
from .models import (
    FarmerAadhaarKYC,
    FarmerProfile,
    BankDetail,
    BuyerBusinessProfile,
    BuyerTraderProfile,
    Wallet
    )
import random
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required

# ---------------------------------------------------------
# ROLE SELECT PAGE
# ---------------------------------------------------------
def select_role(request):
    return render(request, 'accounts/select_role.html')


# ---------------------------------------------------------
# FARMER SIGNUP FLOW
# ---------------------------------------------------------

def farmer_aadhaar(request):
    if request.method == 'POST':
        aadhaar = request.POST.get('aadhaar')

        try:
            kyc = FarmerAadhaarKYC.objects.get(aadhaar_number=aadhaar)
        except FarmerAadhaarKYC.DoesNotExist:
            messages.error(request, "Aadhaar number not found.")
            return render(request, 'accounts/farmer_aadhaar.html')
        print(kyc.otp)
        # store these in session
        request.session['farmer_aadhaar'] = kyc.aadhaar_number
        request.session['farmer_email'] = kyc.email
        request.session['farmer_otp'] = kyc.otp
        subject = "Your Krushi Kisan Suraksha OTP"
        message = (
            f"Dear Farmer,\n\n"
            f"Your One-Time Password (OTP) for Krushi Kisan Suraksha verification is:\n\n"
            f"OTP: {kyc.otp}\n\n"
            "Regards,\n"
            "Krushi Kisan Suraksha Team\n"
            "Ministry of Agriculture & Farmers Welfare"
        )

        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [kyc.email])
        messages.success(request, f"OTP sent to {kyc.email} (Demo OTP: {kyc.otp})")
        return redirect('farmer_otp')

    return render(request, 'accounts/farmer_aadhaar.html')


def farmer_otp(request):
    if request.method == 'POST':
        entered = request.POST.get('otp')
        correct = request.session.get('farmer_otp')
        print("entered post")
        if entered == correct:
            print("check")
            request.session['farmer_otp_verified'] = True
            messages.success(request, "OTP Verified Successfully.")
            return redirect('farmer_register')
        else:
            messages.error(request, "Incorrect OTP. Try again.")

    return render(request, 'accounts/farmer_otp.html')


def farmer_register(request):
    if not request.session.get('farmer_otp_verified'):
        messages.error(request, "Please verify OTP first.")
        return redirect('farmer_aadhaar')

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
 
        password = request.POST.get('password')
        confirm = request.POST.get('confirm')

        mobile = request.POST.get('mobile')
        alt_mobile = request.POST.get('alt_mobile')
        village = request.POST.get('village')
        mandal = request.POST.get('mandal')
        district = request.POST.get('district')
        land_size = request.POST.get('land_size')

        cg = request.POST.get('crop_groundnut') == 'on'
        cs = request.POST.get('crop_soybean') == 'on'
        cf = request.POST.get('crop_sunflower') == 'on'

        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, 'accounts/farmer_register.html')

        # Check if email already used
        if User.objects.filter(username=email).exists():
            messages.error(request, "This email is already registered.")
            return render(request, 'accounts/farmer_register.html')

        # create user with email as username
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=full_name
        )

        # create farmer profile
        aadhaar = request.session.get('farmer_aadhaar')

        FarmerProfile.objects.create(
            user=user,
            aadhaar_number=aadhaar,
            mobile=mobile,
            alternate_mobile=alt_mobile,
            village=village,
            mandal=mandal,
            district=district,
            land_size=land_size,
            grows_groundnut=cg,
            grows_soybean=cs,
            grows_sunflower=cf,
        )

        login(request, user)

        messages.success(request, "Farmer Registration Complete. Add Bank Details.")
        return redirect('farmer_bank')

    return render(request, 'accounts/farmer_register.html')


def farmer_bank(request):
    if not request.user.is_authenticated:
        messages.error(request, "Please login first.")
        return redirect('login')

    if request.method == 'POST':
        holder = request.POST.get('holder')
        bank_name = request.POST.get('bank_name')
        acc_no = request.POST.get('acc_no')
        ifsc = request.POST.get('ifsc')
        upi = request.POST.get('upi')

        bank, created = BankDetail.objects.get_or_create(user=request.user)
        bank.account_holder_name = holder
        bank.bank_name = bank_name
        bank.account_number = acc_no
        bank.ifsc_code = ifsc
        bank.upi_id = upi
        bank.save()

        messages.success(request, "Bank Details Saved Successfully.")

        return redirect('register_success')


    return render(request, 'accounts/farmer_bank.html')



# ---------------------------------------------------------
# BUYER SIGNUP FLOW
# ---------------------------------------------------------

def buyer_email(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        otp = str(random.randint(100000, 999999))
        print(otp)
        request.session['buyer_email'] = email
        request.session['buyer_otp'] = otp
        subject = "Your Krushi Kisan Suraksha OTP"
        message = (
            f"Dear Farmer,\n\n"
            f"Your One-Time Password (OTP) for Krushi Kisan Suraksha verification is:\n\n"
            f"OTP: {otp}\n\n"
            "Regards,\n"
            "Krushi Kisan Suraksha Team\n"
            "Ministry of Agriculture & Farmers Welfare"
        )
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
        messages.success(request, f"OTP sent to {email} (Demo OTP: {otp})")

        return redirect('buyer_otp')

    return render(request, 'accounts/buyer_email.html')


def buyer_otp(request):
    if request.method == 'POST':
        entered = request.POST.get('otp')
        correct = request.session.get('buyer_otp')

        if entered == correct:
            request.session['buyer_otp_verified'] = True
            messages.success(request, "OTP Verified Successfully.")
            return redirect('buyer_type')
        else:
            messages.error(request, "Incorrect OTP. Try again.")

    return render(request, 'accounts/buyer_otp.html')


def buyer_type(request):
    if not request.session.get('buyer_otp_verified'):
        messages.error(request, "Please verify OTP first.")
        return redirect('buyer_email')

    return render(request, 'accounts/buyer_type.html')



def buyer_business(request):
    if not request.session.get('buyer_otp_verified'):
        messages.error(request, "Please verify OTP first.")
        return redirect('buyer_email')

    if request.method == 'POST':
        email = request.session.get('buyer_email')

        full_name = request.POST.get('full_name')
        password = request.POST.get('password')
        confirm = request.POST.get('confirm')

        company_name = request.POST.get('company_name')
        company_type = request.POST.get('company_type')
        gst = request.POST.get('gst')
        business_phone = request.POST.get('business_phone')
        factory_address = request.POST.get('factory_address')
        intake = request.POST.get('intake')

        cg = request.POST.get('crop_groundnut') == 'on'
        cs = request.POST.get('crop_soybean') == 'on'
        cf = request.POST.get('crop_sunflower') == 'on'

        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, 'accounts/buyer_business_info.html')

        if User.objects.filter(username=email).exists():
            messages.error(request, "This email is already registered.")
            return render(request, 'accounts/buyer_business_info.html')

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=full_name
        )

        BuyerBusinessProfile.objects.create(
            user=user,
            company_name=company_name,
            company_type=company_type,
            gst_number=gst,
            business_email=email,
            business_phone=business_phone,
            factory_address=factory_address,
            intake_capacity=intake,
            prefers_groundnut=cg,
            prefers_soybean=cs,
            prefers_sunflower=cf,
        )

        login(request, user)

        messages.success(request, "Business Buyer Profile Created. Add Bank Details.")
        return redirect('buyer_bank')

    return render(request, 'accounts/buyer_business_info.html')



def buyer_trader(request):
    if not request.session.get('buyer_otp_verified'):
        messages.error(request, "Please verify OTP first.")
        return redirect('buyer_email')

    if request.method == 'POST':
        email = request.session.get('buyer_email')

        full_name = request.POST.get('full_name')
        password = request.POST.get('password')
        confirm = request.POST.get('confirm')

        trader_type = request.POST.get('trader_type')
        shop_name = request.POST.get('shop_name')
        license_number = request.POST.get('license')
        capacity = request.POST.get('capacity')

        cg = request.POST.get('crop_groundnut') == 'on'
        cs = request.POST.get('crop_soybean') == 'on'
        cf = request.POST.get('crop_sunflower') == 'on'

        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, 'accounts/buyer_trader_info.html')

        if User.objects.filter(username=email).exists():
            messages.error(request, "This email is already registered.")
            return render(request, 'accounts/buyer_trader_info.html')

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=full_name
        )

        BuyerTraderProfile.objects.create(
            user=user,
            trader_type=trader_type,
            shop_name=shop_name,
            license_number=license_number,
            capacity=capacity,
            prefers_groundnut=cg,
            prefers_soybean=cs,
            prefers_sunflower=cf,
        )

        login(request, user)

        messages.success(request, "Trader Buyer Profile Created. Add Bank Details.")
        return redirect('buyer_bank')

    return render(request, 'accounts/buyer_trader_info.html')



def buyer_bank(request):
    if not request.user.is_authenticated:
        messages.error(request, "Please login first.")
        return redirect('login')

    if request.method == 'POST':
        holder = request.POST.get('holder')
        bank_name = request.POST.get('bank')
        acc_no = request.POST.get('acc_no')
        ifsc = request.POST.get('ifsc')
        upi = request.POST.get('upi')

        bank, created = BankDetail.objects.get_or_create(user=request.user)
        bank.account_holder_name = holder
        bank.bank_name = bank_name
        bank.account_number = acc_no
        bank.ifsc_code = ifsc
        bank.upi_id = upi
        bank.save()

        messages.success(request, "Bank Details Saved Successfully.")
        return redirect('register_success')


    return render(request, 'accounts/buyer_bank.html')




# ---------------------------------------------------------
# LOGIN / LOGOUT
# ---------------------------------------------------------

from django.contrib.auth import authenticate, login, logout

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        # For login, username = email (same for farmer + buyer)
        user = authenticate(request, username=email, password=password)

        if user is None:
            messages.error(request, "Invalid email or password.")
            return render(request, "accounts/login.html")

        login(request, user)

        # --- Identify USER TYPE ---
        from .models import FarmerProfile, BuyerBusinessProfile, BuyerTraderProfile

        # ADMIN LOGIN
        # ADMIN LOGIN → go to custom admin dashboard
        if user.is_staff or user.is_superuser:
            return redirect('/panel/dashboard/')


        # FARMER LOGIN
        if FarmerProfile.objects.filter(user=user).exists():
            return redirect("/farmer/dashboard/")

        # BUYER BUSINESS LOGIN
        if BuyerBusinessProfile.objects.filter(user=user).exists():
            return redirect("/buyer/dashboard/")

        # BUYER TRADER LOGIN
        if BuyerTraderProfile.objects.filter(user=user).exists():
            return redirect("/buyer/dashboard/")

        # If nothing matched (rare)
        messages.error(request, "User type not found.")
        return render(request, "accounts/login.html")

    return render(request, "accounts/login.html")


def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('/accounts/login/')
def register_success(request):
    return render(request, 'accounts/register_success.html')

from django.shortcuts import render, redirect
from django.contrib import messages
from decimal import Decimal
from accounts.models import Wallet

def add_money(request):
    wallet = request.user.wallet

    if request.method == "POST":
        amount_raw = request.POST.get("amount")

        # Validate
        try:
            amount = Decimal(amount_raw)
        except:
            messages.error(request, "Enter a valid amount.")
            return redirect("add_money")

        if amount <= 0:
            messages.error(request, "Amount must be greater than 0.")
            return redirect("add_money")

        # Add to wallet balance
        wallet.balance += amount
        wallet.save()

        messages.success(request, f"₹{amount} added successfully!")
        return redirect("add_money_success")

    return render(request, "wallet/add_money.html", {"wallet": wallet})
def add_money_success(request):
    wallet = request.user.wallet
    return render(request, "wallet/add_money_success.html", {"wallet": wallet})

@login_required
def wallet_add(request):
    """
    Simple Add Money page shared by Farmer & Buyer.
    """
    wallet = request.user.wallet

    if request.method == "POST":
        amount_raw = request.POST.get("amount")

        # Validate input
        try:
            amount = Decimal(amount_raw)
        except:
            messages.error(request, "Please enter a valid amount.")
            return redirect("wallet_add")

        if amount <= 0:
            messages.error(request, "Amount must be greater than ₹0.")
            return redirect("wallet_add")

        # Credit wallet (for hackathon: instant success)
        wallet.balance += amount
        wallet.save()

        messages.success(request, f"₹{amount} added to your wallet successfully.")
        return redirect("wallet_add_success")

    return render(request, "accounts/wallet_add.html", {"wallet": wallet})


@login_required
def wallet_add_success(request):
    """
    Simple success screen after top-up.
    """
    wallet = request.user.wallet
    return render(request, "accounts/wallet_add_success.html", {"wallet": wallet})
