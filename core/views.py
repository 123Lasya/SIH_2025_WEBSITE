from django.shortcuts import render
from django.shortcuts import redirect

def index(request):
    return render(request, 'core/index.html')

def terms(request):
    return render(request, 'core/conditions.html')

def privacy(request):
    return render(request, 'core/privacy.html')

def disclaimer(request):
    return render(request, 'core/disclaimer.html')

def help(request):
    return render(request, 'core/help.html')
def contact(request):
    return render(request, 'core/contact.html')
def faq(request):
    return render(request, 'core/faq.html')
from django.http import JsonResponse
from core.models import MTMHistory

def mtm_chart_api(request):
    crop = request.GET.get("crop")  # optional filter
    user = request.user

    qs = MTMHistory.objects.filter(user=user).order_by("date")

    if crop:
        qs = qs.filter(crop=crop)

    dates = [str(r.date) for r in qs]
    pnl = [float(r.pnl) for r in qs]

    return JsonResponse({
        "dates": dates,
        "pnl": pnl,
        "crop": crop or "All"
    })


def set_language(request):
    """Set `request.session['lang']` and redirect back.

    Accepts `?lang=te|hi|en` and optional `next` parameter to redirect.
    """
    lang = request.GET.get("lang") or request.POST.get("lang")
    next_url = request.GET.get("next") or request.POST.get("next") or request.META.get("HTTP_REFERER") or "/"
    if lang in ("en", "te", "hi"):
        request.session["lang"] = lang
        # also set a cookie as a fallback so client-side and middleware
        # can observe language even if session cookie timing is delayed
        response = redirect(next_url)
        response.set_cookie("lang", lang, max_age=30 * 24 * 3600)
        return response
    return redirect(next_url)
from django.shortcuts import render
from .models import MTMHistory

def farmer_mtm_history(request):
    user = request.user
    history = MTMHistory.objects.filter(user=user).order_by("-date")
    return render(request, "farmer/mtm_history.html", {"history": history})


def buyer_mtm_history(request):
    user = request.user
    history = MTMHistory.objects.filter(user=user).order_by("-date")
    return render(request, "buyer/mtm_history.html", {"history": history})
