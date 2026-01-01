from .models import Alert, FarmerContract
from accounts.models import FarmerProfile
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import JsonResponse
from datetime import datetime, timedelta
from core.ai_utils import predict_price, forecast_next_7_days
from core.matching_engine import run_matching_engine
from core.mtm_engine import run_mtm_engine
from blockchain.ipfs import pin_json_to_ipfs
from blockchain.forward import create_forward_contract_onchain
from blockchain.hedge import create_farmer_hedge_onchain
from django.db.models import Sum, Count, F
import datetime
# from pandas import Sum
def farmer_dashboard(request):
    user = request.user

    # 1️⃣ Alerts (existing)
    alerts = Alert.objects.filter(user=user).order_by('-created_at')[:3]

    # 2️⃣ Wallet summary
    wallet = user.wallet
    available = wallet.available_balance
    locked = wallet.locked_margin

    # 3️⃣ Total MTM PnL
    from core.models import MTMHistory
    total_pnl = MTMHistory.objects.filter(user=user).aggregate(
        Sum("pnl")
    )["pnl__sum"] or 0

    # 4️⃣ Today PnL
    today = datetime.date.today()
    today_pnl = MTMHistory.objects.filter(
        user=user, date=today
    ).aggregate(Sum("pnl"))["pnl__sum"] or 0

    # 5️⃣ Open Hedges Count
    from farmers.models import FarmerHedge
    open_hedges = FarmerHedge.objects.filter(
        farmer__user=user, status="OPEN"
    ).count()

    context = {
        "alerts": alerts,
        "available": available,
        "locked": locked,
        "total_pnl": total_pnl,
        "today_pnl": today_pnl,
        "open_hedges": open_hedges,
    }
    return render(request, 'farmers/dashboard.html', context)



def farmer_create_contract(request):
    warehouses = [
        "Guntur Warehouse (AP)",
        "Nellore Cold Storage",
        "Bhopal Agro Storage",
        "Indore Oilseed Hub"
    ]

    if request.method == "POST":

        crop = request.POST.get("crop")
        quantity = request.POST.get("quantity")
        grade_a = request.POST.get("grade_a")
        grade_b = request.POST.get("grade_b")
        grade_c = request.POST.get("grade_c")
        warehouse = request.POST.get("warehouse")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")

        # 🌟 1. USER PRESSED AI PREDICT
        if "ai_predict" in request.POST:

            # Predict price using ML
            predicted_price = predict_price(crop, start_date)

            # Auto fill Grade A/B/C with predicted values
            grade_a = predicted_price
            grade_b = predicted_price - 100   # Example logic
            grade_c = predicted_price - 200   # Example logic

            return render(request, "farmers/create_contract.html", {
                "crop": crop,
                "quantity": quantity,
                "grade_a": grade_a,
                "grade_b": grade_b,
                "grade_c": grade_c,
                "warehouse": warehouse,
                "start_date": start_date,
                "end_date": end_date,
                "warehouses": warehouses
            })
        if "submit" in request.POST:

            # Validate mandatory grade fields
            if not grade_a or not grade_b or not grade_c:
                messages.error(request, "Please fill all Grade prices or click AI Predict.")
                return render(request, "farmers/create_contract.html", {
                    "crop": crop,
                    "quantity": quantity,
                    "grade_a": grade_a,
                    "grade_b": grade_b,
                    "grade_c": grade_c,
                    "warehouse": warehouse,
                    "start_date": start_date,
                    "end_date": end_date,
                    "warehouses": warehouses
                })

            farmer = FarmerProfile.objects.get(user=request.user)

            # 1️⃣ Save to DB first
            contract = FarmerContract.objects.create(
                farmer=farmer,
                crop=crop,
                quantity=quantity,
                grade_a_price=grade_a,
                grade_b_price=grade_b,
                grade_c_price=grade_c,
                warehouse=warehouse,
                start_date=start_date,
                end_date=end_date,
                buyer_status="PENDING"
            )

            # 2️⃣ Prepare JSON for IPFS
            payload = {
                "app": "Krushi Kisan Suraksha",
                "type": "forward_contract",
                "farmer_uid": str(farmer.farmer_uid),
                "django_contract_id": contract.id,
                "crop": crop,
                "quantity": str(quantity),
                "warehouse": warehouse,
                "grade_prices": {
                    "A": str(grade_a),
                    "B": str(grade_b),
                    "C": str(grade_c),
                },
                "start_date": start_date,
                "end_date": end_date,
            }

            try:
                # 3️⃣ Upload to IPFS via Pinata
                cid = pin_json_to_ipfs(payload)

                # 4️⃣ Call blockchain ForwardSalePOL
                # tx_hash, contract_id = create_forward_contract_onchain(contract, cid)
                # CORRECT
                tx_hash, blockchain_id = create_forward_contract_onchain(contract, cid)


                # 5️⃣ Save chain info back to DB
                contract.blockchain_hash = tx_hash  # or f"{deal_id}:{tx_hash}"
                contract.save()

                messages.success(
                    request,
                    f"Contract submitted & stored on blockchain. Tx: {tx_hash[:10]}..."
                )
            except Exception as e:
                # If any blockchain/IPFS error occur, DB contract still exists
                messages.warning(
                    request,
                    f"Contract saved, but blockchain/IPFS failed: {e}"
                )

            return redirect("farmer_my_contracts")


        # 🌟 2. USER PRESSED SUBMIT CONTRACT
    #     if "submit" in request.POST:

    #         # Validate mandatory grade fields
    #         if not grade_a or not grade_b or not grade_c:
    #             messages.error(request, "Please fill all Grade prices or click AI Predict.")
    #             return render(request, "farmers/create_contract.html", {
    #                 "crop": crop,
    #                 "quantity": quantity,
    #                 "grade_a": grade_a,
    #                 "grade_b": grade_b,
    #                 "grade_c": grade_c,
    #                 "warehouse": warehouse,
    #                 "start_date": start_date,
    #                 "end_date": end_date,
    #                 "warehouses": warehouses
    #             })

    #         farmer = FarmerProfile.objects.get(user=request.user)

    #         FarmerContract.objects.create(
    #             farmer=farmer,
    #             crop=crop,
    #             quantity=quantity,
    #             grade_a_price=grade_a,
    #             grade_b_price=grade_b,
    #             grade_c_price=grade_c,
    #             warehouse=warehouse,
    #             start_date=start_date,
    #             end_date=end_date,
    #             buyer_status="PENDING"
    #         )
            
    #         messages.success(request, "Contract submitted to buyers.")
    #         return redirect("farmer_my_contracts")

    return render(request, "farmers/create_contract.html", {
        "warehouses": warehouses
    })


from django.shortcuts import render, redirect
from django.contrib import messages
from accounts.models import FarmerProfile
from .models import FarmerHedge

from .ai_utils import predict_price
from accounts.models import FarmerProfile
from django.contrib import messages
from .models import FarmerHedge

from decimal import Decimal
from accounts.models import FarmerProfile, Wallet

def farmer_create_hedge(request):
    if request.method == "POST":

        crop = request.POST.get("crop")
        quantity_raw = request.POST.get("quantity")
        end_date = request.POST.get("end_date")
        hedge_price_raw = request.POST.get("hedge_price")
        hedge_type = request.POST.get("hedge_type")

        # Convert safely to Decimal
        try:
            quantity = Decimal(quantity_raw)
            hedge_price = Decimal(hedge_price_raw)
        except:
            messages.error(request, "Please enter valid numeric values.")
            return render(request, "farmers/create_hedge.html", {
                "crop": crop,
                "quantity": quantity_raw,
                "hedge_type": hedge_type,
                "end_date": end_date,
                "predicted_price": hedge_price_raw,
            })

        # 1️ AI Predict button
        if "ai_predict" in request.POST:
            predicted_price = predict_price(crop, end_date)
            return render(request, "farmers/create_hedge.html", {
                "crop": crop,
                "quantity": quantity,
                "end_date": end_date,
                "predicted_price": predicted_price,
            })

        # 2 Submit Hedge
        # Instead of creating the hedge directly, save data temporarily
        request.session["hedge_form"] = {
            "crop": crop,
            "quantity": float(quantity),
            "end_date": end_date,
            "hedge_price": float(hedge_price)
        } 

        return redirect("farmer_hedge_confirm")

        # -----------------------------
        # MARGIN LOGIC (10% of value)
        # -----------------------------
        hedge_value = quantity * hedge_price       # total value
        margin_rate = Decimal("0.10")              # 🔹 10% margin
        margin_amount = (hedge_value * margin_rate).quantize(Decimal("1.00"))

        # Get farmer + wallet
        farmer = FarmerProfile.objects.get(user=request.user)
        wallet = request.user.wallet

        # Check if wallet has enough available balance
        if wallet.available_balance < margin_amount:
            messages.error(
                request,
                f"Not enough wallet balance. Required margin: ₹{margin_amount}, "
                f"Available: ₹{wallet.available_balance}."
            )
            return render(request, "farmers/create_hedge.html", {
                "crop": crop,
                "quantity": quantity,
                "end_date": end_date,
                "predicted_price": hedge_price,
            })

        # Lock margin (do NOT reduce balance, only increase locked_margin)
        wallet.locked_margin += margin_amount
        wallet.save()

        # Save hedge with margin
        FarmerHedge.objects.create(
            farmer=farmer,
            crop=crop,
            quantity=quantity,
            end_date=end_date,
            hedge_price=hedge_price,
            margin_amount=margin_amount,
            status="OPEN",           # if you have this field
            matched_quantity=0,      # if you have this field
        )
        run_matching_engine()

        messages.success(request, f"Hedge created successfully. Margin ₹{margin_amount} locked.")
        return redirect("farmer_my_hedges")

    # GET request → show empty form
    return render(request, "farmers/create_hedge.html")

from decimal import Decimal
from accounts.models import Wallet
from .models import FarmerHedge
from accounts.models import FarmerProfile

def farmer_hedge_margin_preview(request):
    data = request.session.get("hedge_form")

    if not data:
        messages.error(request, "No hedge data found. Please create hedge again.")
        return redirect("farmer_create_hedge")

    crop = data["crop"]
    quantity = Decimal(data["quantity"])
    hedge_price = Decimal(data["hedge_price"])

    hedge_value = quantity * hedge_price
    margin = (hedge_value * Decimal("0.10")).quantize(Decimal("1.00"))

    wallet = request.user.wallet

    can_proceed = wallet.available_balance >= margin

    return render(request, "farmers/hedge_margin_preview.html", {
        "crop": crop,
        "quantity": quantity,
        "hedge_price": hedge_price,
        "end_date": data["end_date"],
        "hedge_value": hedge_value,
        "margin": margin,
        "wallet": wallet,
        "can_proceed": can_proceed,
    })
def farmer_hedge_confirm(request):
    data = request.session.get("hedge_form")

    if not data:
        messages.error(request, "No hedge data found.")
        return redirect("farmer_create_hedge")

    crop = data["crop"]
    quantity = Decimal(data["quantity"])
    hedge_price = Decimal(data["hedge_price"])
    end_date = data["end_date"]

    hedge_value = quantity * hedge_price
    margin = (hedge_value * Decimal("0.10")).quantize(Decimal("1.00"))

    # wallet = request.user.wallet

    # # Check funds again
    # if wallet.available_balance < margin:
    #     messages.error(request, "Insufficient balance. Please add money.")
    #     return redirect("farmer_hedge_margin_preview")

    # # Lock margin
    # wallet.locked_margin += margin
    # wallet.save()

    # Create real hedge
    farmer = FarmerProfile.objects.get(user=request.user)

    hedge = FarmerHedge.objects.create(
        farmer=farmer,
        crop=crop,
        quantity=quantity,
        end_date=end_date,
        hedge_price=hedge_price,
        margin_amount=margin,
        matched_quantity=0,
        status="OPEN",
    )

    # CALL BLOCKCHAIN HERE
    try:
        tx_hash = create_farmer_hedge_onchain(hedge)
        hedge.hedge_hash = tx_hash
        hedge.save()
        messages.success(
            request,
            f"Hedge created successfully on blockchain. Tx: {tx_hash}"
        )
    except Exception as e:
        messages.warning(
            request,
            f"Hedge saved in system, but blockchain transaction failed: {e}"
        )

    # Clear session
    if "hedge_form" in request.session:
        del request.session["hedge_form"]

    return redirect("farmer_my_hedges")




def farmer_my_contracts(request):
    farmer = FarmerProfile.objects.get(user=request.user)
    contracts = FarmerContract.objects.filter(farmer=farmer).order_by('-created_at')
    return render(request, 'farmers/my_contracts.html', {'contracts': contracts})



def farmer_my_hedges(request):
    farmer = FarmerProfile.objects.get(user=request.user)
    hedges = FarmerHedge.objects.filter(farmer=farmer).order_by('-created_at')
    return render(request, 'farmers/my_hedges.html', {'hedges': hedges})


def farmer_contract_detail(request, contract_id):
    contract = get_object_or_404(FarmerContract, id=contract_id)

    alerts = Alert.objects.filter(user=request.user, contract=contract, is_read=False)
    for a in alerts:
        a.is_read = True
        a.save()

    return render(request, "farmers/contract_detail.html", {"contract": contract})





def farmer_alerts(request):
    alerts = Alert.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'farmers/alerts.html', {'alerts': alerts})



def farmer_education(request):
    # Later you can move this to DB.
    videos = [
        {
            "title": "What is Hedging?",
            "description": "Basic introduction to hedging for farmers.",
            "url": "https://drive.google.com/file/d/1jcaemVu64C3LmCD7kcZUWeXYfmlYcQUn/view?usp=sharing",
        },
        {
            "title": "Understanding Margin & Risk",
            "description": "Explains margin, leverage and risk in simple language.",
            "url": "https://drive.google.com/file/d/1AtDQ7dZXWK-b1TOgf1irQZa4CODWx7O3/view?usp=sharing",
        },
        {
            "title": "Farmer Forward Contracts",
            "description": "How contracts protect you from price volatility.",
            "url": "https://www.youtube.com/embed/VIDEO_ID_3",
        },
    ]
    return render(request, 'farmers/education.html', {"videos": videos})


def farmer_gov_support(request):
    schemes = [
        {
            "name": "PM-KISAN",
            "description": "Income support scheme for small and marginal farmers.",
            "link": "https://www.pmkisan.gov.in/",
        },
        {
            "name": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
            "description": "Crop insurance scheme for protection against crop loss.",
            "link": "https://pmfby.gov.in/",
        },
        {
            "name": "e-NAM",
            "description": "National Agriculture Market for transparent price discovery.",
            "link": "https://enam.gov.in/",
        },
    ]
    return render(request, 'farmers/gov_support.html', {"schemes": schemes})



from accounts.models import FarmerProfile, BankDetail

def farmer_profile(request):
    farmer = FarmerProfile.objects.get(user=request.user)
    bank = BankDetail.objects.filter(user=request.user).first()
    return render(request, 'farmers/profile.html', {'farmer': farmer, 'bank': bank})
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET", "POST"])
def farmer_profile_edit(request):
    farmer = FarmerProfile.objects.get(user=request.user)

    if request.method == "POST":
        # Update basic details
        farmer.mobile = request.POST.get("mobile")
        farmer.alternate_mobile = request.POST.get("alt_mobile")
        farmer.village = request.POST.get("village")
        farmer.mandal = request.POST.get("mandal")
        farmer.district = request.POST.get("district")
        farmer.land_size = request.POST.get("land_size")

        # Update crop preferences
        farmer.grows_groundnut = (request.POST.get("crop_groundnut") == "on")
        farmer.grows_soybean = (request.POST.get("crop_soybean") == "on")
        farmer.grows_sunflower = (request.POST.get("crop_sunflower") == "on")

        farmer.save()

        messages.success(request, "Profile updated successfully!")
        return redirect("farmer_profile")

    return render(request, "farmers/profile_edit.html", {"farmer": farmer})

def get_forecast_data(request):
    crop = request.GET.get("crop", "Groundnut")

    predictions = forecast_next_7_days(crop)

    dates = [p["date"] for p in predictions]
    prices = [p["price"] for p in predictions]

    return JsonResponse({
        "dates": dates,
        "prices": prices,
        "crop": crop
    })
from core.models import MTMHistory

def farmer_mtm_history(request):
    records = MTMHistory.objects.filter(user=request.user).order_by("-date")

    # Filters (optional)
    crop = request.GET.get("crop")
    if crop:
        records = records.filter(crop=crop)

    date_from = request.GET.get("from")
    date_to = request.GET.get("to")

    if date_from:
        records = records.filter(date__gte=date_from)
    if date_to:
        records = records.filter(date__lte=date_to)

    return render(request, "farmers/mtm_history.html", {
        "records": records,
    })
from core.models import MTMRecord
from farmers.models import FarmerHedge

def farmer_hedge_detail(request, hedge_id):
    hedge = get_object_or_404(FarmerHedge, id=hedge_id, farmer__user=request.user)

    # Fetch MTM history for this hedge only
    records = MTMRecord.objects.filter(
        hedge_id=hedge_id,
        user=request.user
    ).order_by("date")

    # Prepare chart data
    dates = [str(r.date) for r in records]
    pnl = [float(r.pnl) for r in records]

    total_pnl = sum([r.pnl for r in records]) if records else 0

    return render(request, "farmers/hedge_detail.html", {
            "hedge": hedge,
            "records": records,
            "dates": dates,
            "pnl": pnl,
            "total_pnl": total_pnl,
    })
from django.http import JsonResponse
from core.ai_utils import predict_price

def ajax_predict_price(request):
    crop = request.GET.get("crop")
    end_date = request.GET.get("end_date")

    if not crop or not end_date:
        return JsonResponse({"error": "Missing parameters"}, status=400)

    predicted = predict_price(crop, end_date)
    return JsonResponse({"predicted_price": predicted})

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from core.models import MTMHistory

@login_required
def farmer_mtm_history(request):
    history = MTMHistory.objects.filter(
        user=request.user
    ).order_by('-date', '-id')

    return render(request, "farmer/mtm_history.html", {
        "history": history
    })
