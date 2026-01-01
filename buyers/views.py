
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
from core.ai_utils import predict_price, forecast_next_7_days
from core.matching_engine import run_matching_engine
from core.mtm_engine import run_mtm_engine
from blockchain.forward import create_forward_contract_onchain
from blockchain.hedge import create_buyer_hedge_onchain
from django.db.models import Sum, Count, F
import datetime

# @login_required
# def buyer_dashboard(request):
#     # Default crop or crop selected by user
#     crop = request.GET.get("crop", "Groundnut")

#     # Dummy 7-day forecast (replace with ML later)
#     dummy_forecasts = {
#         "Groundnut": [5400, 5450, 5520, 5600, 5580, 5620, 5700],
#         "Soybean":   [4800, 4820, 4850, 4900, 4880, 4950, 5000],
#         "Sunflower": [6200, 6220, 6250, 6300, 6280, 6350, 6400],
#     }

#     forecast = dummy_forecasts.get(crop, dummy_forecasts["Groundnut"])

#     return render(request, "buyers/dashboard.html", {
#         "crop": crop,
#         "forecast": forecast,
#     })

# ----------------------------
#  1. BUYER DASHBOARD
# ----------------------------

@login_required
def buyer_dashboard(request):
    user = request.user

    # Wallet
    wallet = user.wallet
    available = wallet.available_balance
    locked = wallet.locked_margin

    # MTM totals
    from core.models import MTMHistory
    total_pnl = MTMHistory.objects.filter(user=user).aggregate(
        Sum("pnl")
    )["pnl__sum"] or 0

    today = datetime.date.today()
    today_pnl = MTMHistory.objects.filter(
        user=user, date=today
    ).aggregate(Sum("pnl"))["pnl__sum"] or 0
 
    # Open buyer hedges
    from buyers.models import BuyerHedge
    open_hedges = BuyerHedge.objects.filter(
        buyer=user, status="OPEN"
    ).count()

    # Forecast (existing)
    crop = request.GET.get("crop", "Groundnut")
    predictions = forecast_next_7_days(crop)
    prices = [p["price"] for p in predictions]
    dates = [p["date"] for p in predictions]

    return render(request, "buyers/dashboard.html", {
        "crop": crop,
        "forecast": prices,
        "dates": dates,
        "forecast_js": json.dumps(prices),
        "today_pnl": today_pnl,
        "total_pnl": total_pnl,
        "open_hedges": open_hedges,
        "available": available,
    })





# ----------------------------
#  2. CREATE HEDGE
# ----------------------------

from decimal import Decimal
from accounts.models import Wallet
from buyers.models import BuyerHedge
from core.ai_utils import predict_price
from django.contrib import messages
from django.contrib.auth.decorators import login_required

@login_required
def buyer_create_hedge(request):
    if request.method == "POST":

        crop = request.POST.get("crop")
        quantity_raw = request.POST.get("quantity")
        end_date = request.POST.get("end_date")
        hedge_price_raw = request.POST.get("hedge_price")
        hedge_type = request.POST.get("hedge_type")

        # Convert safe numeric values
        try:
            quantity = Decimal(quantity_raw)
            hedge_price = Decimal(hedge_price_raw)
        except:
            messages.error(request, "Please enter valid numbers.")
            return render(request, "buyer/create_hedge.html", {
                "crop": crop, "quantity": quantity_raw,
                "end_date": end_date, "predicted_price": hedge_price_raw
            })

        # 1 AI Predict button
        if "ai_predict" in request.POST:
            predicted_price = predict_price(crop, end_date)
            return render(request, "buyer/create_hedge.html", {
                "crop": crop,
                "quantity": quantity,
                "end_date": end_date,
                "hedge_type":hedge_type,
                "predicted_price": predicted_price
            })

        # 2️ Submit Hedge
        request.session["hedge_form"] = {
            "crop": crop,
            "quantity": float(quantity),
            "end_date": end_date,
            "hedge_price": float(hedge_price)
        }

        return redirect("buyer_hedge_confirm")
        # if quantity <= 0 or hedge_price <= 0:
        #     messages.error(request, "Quantity and price must be positive.")
        #     return render(request, "buyers/create_hedge.html", {
        #         "crop": crop, "quantity": quantity,
        #         "end_date": end_date, "predicted_price": hedge_price
        #     })

        # -----------------------------
        # MARGIN CALCULATION (10%)
        # -----------------------------
        hedge_value = quantity * hedge_price
        margin_rate = Decimal("0.10")
        margin_amount = (hedge_value * margin_rate).quantize(Decimal("1.00"))

        buyer = BuyerBusinessProfile.objects.get(user=request.user) | BuyerTraderProfile.objects.get(user=request.user)         # ✅ buyer is User
        wallet = request.user.wallet         # ✅ same as farmer.wallet

        # Check wallet balance
        if wallet.available_balance < margin_amount:
            messages.error(
                request,
                f"Insufficient wallet balance. Required ₹{margin_amount}, "
                f"Available ₹{wallet.available_balance}. Please add money."
            )
            return render(request, "buyers/create_hedge.html", {
                "crop": crop,
                "quantity": quantity,
                "end_date": end_date,
                "predicted_price": hedge_price
            })

        # Lock margin (do NOT reduce balance)
        wallet.locked_margin += margin_amount
        wallet.save()

        # Save hedge
        # BuyerHedge.objects.create(
        #     buyer=buyer,              # ✅ FK to User
        #     crop=crop,
        #     quantity=quantity,
        #     end_date=end_date,
        #     hedge_price=hedge_price,
        #     margin_amount=margin_amount,
        #     status="OPEN",
        #     matched_quantity=0
        # )

        # from core.matching_engine import run_matching_engine
        # run_matching_engine()

        # messages.success(request, f"Hedge created successfully. Margin ₹{margin_amount} locked.")
        # return redirect("buyer_my_hedges")
        BuyerHedge.objects.create(
            buyer=buyer,
            crop=crop,
            quantity=quantity,
            end_date=end_date,
            hedge_price=hedge_price,
            margin_amount=margin_amount,
            status="OPEN",
            matched_quantity=0
        )
        from core.matching_engine import run_matching_engine
        run_matching_engine()

        messages.success(request, f"Hedge created successfully. Margin ₹{margin_amount} locked.")
        # 🔗 CALL BLOCKCHAIN
        try:
            print("entered")
            tx_hash = create_buyer_hedge_onchain(hedge)
            hedge.hedge_hash = tx_hash
            hedge.save()
            messages.success(
                request,
                f"Hedge created on blockchain. Tx: {tx_hash}"
            )
        except Exception as e:
            print("error")
            messages.warning(
                request,
                f"Hedge saved, but blockchain transaction failed: {e}"
            )
        return redirect("buyer_my_hedges")


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
    contract.buyer_status = "BUYER_ACCEPTED"
    contract.contract_status = "PENDING"
    contract.save()

    # 🔗 SEND TO BLOCKCHAIN + IPFS
    try:
        tx_hash = create_forward_contract_onchain(contract)
        contract.blockchain_hash = tx_hash
        contract.save()
    except Exception as e:
        messages.warning(
            request,
            f"Contract accepted, but blockchain tx failed: {e}"
        )

    # Notify farmer
    Alert.objects.create(
        user=contract.farmer.user,
        message=f"Buyer {request.user.username} has shown interest in your contract #{contract.id}.",
        contract=contract,
    )

    messages.success(request, "You accepted this contract. Blockchain tx submitted.")
    return redirect("buyer_my_contracts")

    # Update contract status
    # contract.buyer = request.user
    # contract.buyer_status = "BUYER_ACCEPTED"    # FIXED
    # contract.contract_status = "PENDING"
    # contract.save()

    # # Notify farmer
    # Alert.objects.create(
    #     user=contract.farmer.user,
    #     message=f"Buyer {request.user.username} has shown interest in your contract #{contract.id}.",
    #     contract=contract,
    # )

    # messages.success(request, "You accepted this contract. Waiting for farmer approval.")
    # return redirect("buyer_my_contracts")



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
            contract.buyer_status = "BUYER_ACCEPTED"
            contract.contract_status = "PENDING"
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


    return render(request, "buyers/contract_detail.html", {
        "contract": contract
    })
from core.models import MTMHistory

def buyer_mtm_history(request):
    records = MTMHistory.objects.filter(user=request.user).order_by("-date")

    crop = request.GET.get("crop")
    if crop:
        records = records.filter(crop=crop)

    date_from = request.GET.get("from")
    date_to = request.GET.get("to")

    if date_from:
        records = records.filter(date__gte=date_from)
    if date_to:
        records = records.filter(date__lte=date_to)

    return render(request, "buyers/mtm_history.html", {
        "records": records,
    })
from core.models import MTMRecord

@login_required
def buyer_hedge_detail(request, hedge_id):
    hedge = get_object_or_404(BuyerHedge, id=hedge_id, buyer=request.user)

    # Fetch MTM history for this hedge only
    records = MTMRecord.objects.filter(
        hedge_id=hedge_id,
        user=request.user
    ).order_by("date")

    # Prepare chart data
    dates = [str(r.date) for r in records]
    pnl = [float(r.pnl) for r in records]

    total_pnl = sum([r.pnl for r in records]) if records else 0

    return render(request, "buyers/hedge_detail.html", {
            "hedge": hedge,
            "records": records,
            "dates": dates,
            "pnl": pnl,
            "total_pnl": total_pnl,
    })
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
from core.models import MTMHistory
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from core.models import MTMHistory

@login_required
def buyer_mtm_history(request):
    history = MTMHistory.objects.filter(
        user=request.user
    ).order_by('-date', '-id')

    return render(request, "buyer/mtm_history.html", {
        "history": history
    })
 