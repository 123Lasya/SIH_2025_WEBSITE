from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from core.models import MTMHistory
from accounts.models import FarmerProfile

@login_required
def farmer_mtm_history(request):
    farmer = FarmerProfile.objects.get(user=request.user)

    # Fetch all MTM entries for this farmer
    records = MTMHistory.objects.filter(
        user=request.user
    ).order_by("-date", "-id")

    crop = request.GET.get("crop")
    if crop:
        records = records.filter(crop=crop)

    return render(request, "farmers/mtm_history.html", {
        "records": records,
    })
