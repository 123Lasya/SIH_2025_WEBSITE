# from django.urls import path
# from . import views

# urlpatterns = [
#     path('ok/', views.buyer_ok, name='buyer_ok'),
#     path('dashboard/', views.buyer_dashboard, name='buyer_dashboard'),
# ]
# from django.urls import path
# from . import views

from django.urls import path
from . import views
 
urlpatterns = [
    path('dashboard/', views.buyer_dashboard, name='buyer_dashboard'),

    # Hedges
    path('create-hedge/', views.buyer_create_hedge, name='buyer_create_hedge'),
    path('my-hedges/', views.buyer_my_hedges, name='buyer_my_hedges'),

    # Contracts
    path('my-contracts/', views.buyer_my_contracts, name='buyer_my_contracts'),
    path('contract-lookup/', views.buyer_contract_lookup, name='buyer_contract_lookup'),
    path('accept/<int:contract_id>/', views.buyer_accept_contract, name='buyer_accept_contract'),
 
    # Alerts
    path('alerts/', views.buyer_alerts, name='buyer_alerts'),
    path("alerts/<int:alert_id>/view/", views.buyer_alert_view, name="buyer_alert_view"),

    # Profile
    path('profile/', views.buyer_profile, name='buyer_profile'),
    path('profile/edit/', views.buyer_profile_edit, name='buyer_profile_edit'),
    path("contracts/", views.buyer_contract_lookup, name="buyer_contract_lookup"),
    path("my-contracts/", views.buyer_my_contracts, name="buyer_my_contracts"),
    path("contracts/<int:contract_id>/", views.buyer_contract_detail,name="buyer_contract_detail"), 
    path("mtm-history/", views.buyer_mtm_history, name="buyer_mtm_history"),
    path("hedge/<int:hedge_id>/", views.buyer_hedge_detail, name="buyer_hedge_detail"),

]
