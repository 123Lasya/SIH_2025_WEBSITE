from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.admin_dashboard, name="admin_dashboard"),

    path("farmers/", views.admin_farmers, name="admin_farmers"),
    path("buyers/", views.admin_buyers, name="admin_buyers"),
    path("contracts/", views.admin_contracts, name="admin_contracts"),
    path("hedges/", views.admin_hedges, name="admin_hedges"),
    path("alerts/", views.admin_alerts, name="admin_alerts"),
    path("export/farmers/csv/", views.export_farmers_csv, name="admin_export_farmers_csv"),
    path("export/farmers/excel/", views.export_farmers_excel, name="admin_export_farmers_excel"),

    path("export/buyers/csv/", views.export_buyers_csv, name="admin_export_buyers_csv"),
    path("export/buyers/excel/", views.export_buyers_excel, name="admin_export_buyers_excel"),

    path("export/contracts/csv/", views.export_contracts_csv, name="admin_export_contracts_csv"),
    path("export/contracts/excel/", views.export_contracts_excel, name="admin_export_contracts_excel"),
    path("hedge-summary/", views.admin_hedge_summary, name="admin_hedge_summary"),

    path("export/hedges/csv/", views.export_hedges_csv, name="admin_export_hedges_csv"),
    path("export/hedges/excel/", views.export_hedges_excel, name="admin_export_hedges_excel"),
]
