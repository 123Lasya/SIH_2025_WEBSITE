# from django.shortcuts import render


# from django.shortcuts import render
# from django.contrib.auth.decorators import login_required


# @login_required
# def buyer_dashboard(request):
#     return render(request, 'buyers/dashboard.html')

# # Create your views here.
# def buyer_ok(request):
#     return render(request, 'accounts/buyer_ok.html')
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import json
from farmers.models import FarmerContract, Alert
import datetime
from django.contrib.auth.decorators import login_required
from accounts.models import BuyerBusinessProfile, BuyerTraderProfile
from buyers.models import BuyerHedge  # this is your new model

# dummy prediction function (replace with ML later)
def predict_price(crop, date):
    return 5000  # simple fallback

@login_required
def buyer_dashboard(request):
    # Default crop or crop selected by user
    crop = request.GET.get("crop", "Groundnut")

    # Dummy 7-day forecast (replace with ML later)
    dummy_forecasts = {
        "Groundnut": [5400, 5450, 5520, 5600, 5580, 5620, 5700],
        "Soybean":   [4800, 4820, 4850, 4900, 4880, 4950, 5000],
        "Sunflower": [6200, 6220, 6250, 6300, 6280, 6350, 6400],
    }

    forecast = dummy_forecasts.get(crop, dummy_forecasts["Groundnut"])

    return render(request, "buyers/dashboard.html", {
        "crop": crop,
        "forecast": forecast,
    })

# ----------------------------
#  1. BUYER DASHBOARD
# ----------------------------

@login_required
@login_required
def buyer_dashboard(request):

    # 1) Crop selection (default = Groundnut)
    crop = request.GET.get("crop", "Groundnut")

    # 2) Dummy forecast values (replace with ML later)
    if crop == "Groundnut":
        forecast = [5400, 5450, 5500, 5530, 5580, 5600, 5650]

    elif crop == "Soybean":
        forecast = [4800, 4820, 4850, 4900, 4930, 4950, 5000]

    elif crop == "Sunflower":
        forecast = [6100, 6120, 6150, 6200, 6230, 6250, 6300]

    # 3) Convert to JS-friendly list
    forecast_js = json.dumps(forecast)

    return render(request, "buyers/dashboard.html", {
        "crop": crop,
        "forecast": forecast,
        "forecast_js": forecast_js,
    })



# ----------------------------
#  2. CREATE HEDGE
# ----------------------------

@login_required
def buyer_create_hedge(request):
    if request.method == "POST":
        crop = request.POST.get("crop")
        quantity = request.POST.get("quantity")
        hedge_price = request.POST.get("hedge_price")
        end_date = request.POST.get("end_date")

        BuyerHedge.objects.create(
            buyer=request.user,  # MUST be User
            crop=crop,
            quantity=quantity,
            hedge_price=hedge_price,
            end_date=end_date
        )

        return redirect("buyer_my_hedges")

    return render(request, "buyers/create_hedge.html")

# ----------------------------
#  3. MY HEDGES
# ----------------------------

@login_required
def buyer_my_hedges(request):
    buyer = request.user  # MUST be User instance

    hedges = BuyerHedge.objects.filter(buyer=buyer).order_by("-id")

    return render(request, "buyers/my_hedges.html", {"hedges": hedges})



# ----------------------------
#  4. MY CONTRACTS
# ----------------------------

@login_required
def buyer_my_contracts(request):
    # fetch contracts accepted by this buyer
    contracts = FarmerContract.objects.filter(buyer=request.user)

    return render(request, "buyers/my_contracts.html", {
        "contracts": contracts
    })


# ----------------------------
#  5. CONTRACT LOOKUP (DISTRICT MATCH)
# ----------------------------
def match_district(farmer, buyer_profile):
    farmer_district = farmer.district.lower()

    # Trader Buyer
    if hasattr(buyer_profile, "district"):
        return buyer_profile.district.lower() == farmer_district

    # Business Buyer
    if hasattr(buyer_profile, "factory_address"):
        return farmer_district in buyer_profile.factory_address.lower()

    return False

@login_required
def buyer_contract_lookup(request):
    user = request.user

    # Identify buyer type
    buyer_trader = getattr(user, "buyertraderprofile", None)
    buyer_business = getattr(user, "buyerbusinessprofile", None)

    buyer_profile = buyer_trader if buyer_trader else buyer_business

    if not buyer_profile:
        messages.error(request, "No buyer profile found.")
        return render(request, "buyers/contract_lookup.html", {"contracts": []})

    matched_contracts = []

    # Fetch all farmer contracts where buyer hasn't accepted yet
    all_contracts = FarmerContract.objects.filter(buyer_status="PENDING")

    for contract in all_contracts:
        farmer = contract.farmer  # FarmerProfile

        if match_district(farmer, buyer_profile):
            matched_contracts.append(contract)

    return render(request, "buyers/contract_lookup.html", {
        "contracts": matched_contracts
})



# ----------------------------
#  6. BUYER ACCEPT CONTRACT
# ----------------------------

@login_required
def buyer_accept_contract(request, contract_id):
    contract = get_object_or_404(FarmerContract, id=contract_id)

    contract.buyer = request.user
    contract.buyer_status = "ACCEPTED"
    contract.save()

    # Send alert to farmer
    Alert.objects.create(
        user=contract.farmer.user,
        message=f"Your contract #{contract.id} was ACCEPTED by Buyer {request.user.username}.",
        contract=contract,
    )

    messages.success(request, "Contract accepted successfully!")
    return redirect("buyer_my_contracts")


# ----------------------------
#  7. ALERTS
# ----------------------------

from farmers.models import Alert, FarmerContract
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

@login_required
def buyer_alerts(request):
    alerts = Alert.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "buyers/alerts.html", {"alerts": alerts})

@login_required
def buyer_alert_view(request, alert_id):
    alert = get_object_or_404(Alert, id=alert_id, user=request.user)

    # mark alert as read
    alert.is_read = True
    alert.save()

    # if alert has a linked contract → show details
    if alert.contract:
        return redirect("buyer_contract_detail", contract_id=alert.contract.id)

    return redirect("buyer_alerts")


# ----------------------------
#  8. PROFILE + EDIT PROFILE
# ----------------------------

from django.contrib.auth.decorators import login_required

@login_required
def buyer_profile(request):
    buyer = (
        BuyerBusinessProfile.objects.filter(user=request.user).first()
        or BuyerTraderProfile.objects.filter(user=request.user).first()
    )

    if not buyer:
        return render(request, "buyers/error.html", {"message": "Buyer profile not found"})

    return render(request, "buyers/profile.html", {"buyer": buyer})



@login_required
def buyer_profile_edit(request):
    buyer = (
        BuyerBusinessProfile.objects.filter(user=request.user).first()
        or BuyerTraderProfile.objects.filter(user=request.user).first()
    )

    if not buyer:
        return render(request, "buyers/error.html", {"message": "Buyer profile not found"})

    if request.method == "POST":
        buyer.name = request.POST.get("name")
        buyer.mobile = request.POST.get("mobile")
        buyer.district = request.POST.get("district")
        buyer.address = request.POST.get("address")

        # extra fields (optional)
        if hasattr(buyer, "gst_number"):
            buyer.gst_number = request.POST.get("gst_number")

        if hasattr(buyer, "shop_name"):
            buyer.shop_name = request.POST.get("shop_name")

        buyer.save()
        return redirect("buyer_profile")

    return render(request, "buyers/profile_edit.html", {"buyer": buyer})


@login_required
def buyer_contract_detail(request, contract_id):
    contract = get_object_or_404(FarmerContract, id=contract_id)

    if request.method == "POST":

        action = request.POST.get("action")

        if action == "ACCEPT":
            contract.buyer = request.user
            contract.buyer_status = "ACCEPTED"
            contract.save()

            # alert farmer
            Alert.objects.create(
                user=contract.farmer.user,
                contract=contract,
                message=f"Your contract #{contract.id} has been accepted by {request.user.username}."
            )

            return redirect("buyer_contract_lookup")

        elif action == "REJECT":
            contract.buyer_status = "REJECTED"
            contract.save()
            return redirect("buyer_contract_lookup")

    return render(request, "buyers/contract_detail.html", {
        "contract": contract
    })
