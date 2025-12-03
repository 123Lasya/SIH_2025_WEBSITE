from django.urls import path
from . import views

urlpatterns = [

    # FARMER DASHBOARD
    path('dashboard/', views.farmer_dashboard, name='farmer_dashboard'),
 
    # CONTRACT FLOW
    path('create-contract/', views.farmer_create_contract, name='farmer_create_contract'),
    path('my-contracts/', views.farmer_my_contracts, name='farmer_my_contracts'),
    path('contract/<int:contract_id>/', views.farmer_contract_detail, name='farmer_contract_detail'),

    # HEDGE FLOW
    path('create-hedge/', views.farmer_create_hedge, name='farmer_create_hedge'),
    path('my-hedges/', views.farmer_my_hedges, name='farmer_my_hedges'),
 
    # ALERTS
    path('alerts/', views.farmer_alerts, name='farmer_alerts'),

    # EDUCATION
    path('education/', views.farmer_education, name='farmer_education'),

    # GOV SUPPORT
    path('gov-support/', views.farmer_gov_support, name='farmer_gov_support'),

    # PROFILE VIEW + EDIT
    path('profile/', views.farmer_profile, name='farmer_profile'),
    path('profile/edit/', views.farmer_profile_edit, name='farmer_profile_edit'),
     path("forecast-api/", views.get_forecast_data, name="forecast_api"),
]
