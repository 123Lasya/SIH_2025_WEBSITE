from .models import Alert, FarmerContract
from accounts.models import FarmerProfile
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import JsonResponse
from datetime import datetime, timedelta

def farmer_dashboard(request):
    alerts = Alert.objects.filter(user=request.user).order_by('-created_at')[:3]
    return render(request, 'farmers/dashboard.html', {'alerts': alerts})
def predict_price(crop, date):
    # Temporary dummy prediction logic
    return 5500  # You can change this



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

        # 🌟 2. USER PRESSED SUBMIT CONTRACT
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

            FarmerContract.objects.create(
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

            messages.success(request, "Contract submitted to buyers.")
            return redirect("farmer_my_contracts")

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

def farmer_create_hedge(request):
    if request.method == "POST":

        crop = request.POST.get("crop")
        quantity = request.POST.get("quantity")
        end_date = request.POST.get("end_date")
        hedge_price = request.POST.get("hedge_price")

        # If AI Predict Button Clicked
        if "ai_predict" in request.POST:
            predicted_price = predict_price(crop, end_date)

            return render(request, "farmers/create_hedge.html", {
                "crop": crop,
                "quantity": quantity,
                "end_date": end_date,
                "predicted_price": predicted_price
            })

        # If Submit Button Clicked
        farmer = FarmerProfile.objects.get(user=request.user)
        FarmerHedge.objects.create(
            farmer=farmer,
            crop=crop,
            quantity=quantity,
            end_date=end_date,
            hedge_price=hedge_price
        )

        messages.success(request, "Hedge created successfully!")
        return redirect("farmer_my_hedges")

    return render(request, "farmers/create_hedge.html")



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
            "url": "https://www.youtube.com/embed/VIDEO_ID_1",
        },
        {
            "title": "Understanding Margin & Risk",
            "description": "Explains margin, leverage and risk in simple language.",
            "url": "https://www.youtube.com/embed/VIDEO_ID_2",
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

    # Next 7 days
    dates = [(datetime.today() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]

    # Dummy forecast until ML model is added
    if crop == "Groundnut":
        prices = [6500, 6520, 6540, 6550, 6580, 6600, 6620]
    elif crop == "Soybean":
        prices = [5100, 5120, 5150, 5180, 5200, 5220, 5250]
    elif crop == "Sunflower":
        prices = [7200, 7180, 7150, 7170, 7200, 7220, 7250]
    else:
        prices = [0, 0, 0, 0, 0, 0, 0]

    return JsonResponse({
        "dates": dates,
        "prices": prices,
        "crop": crop
    })
