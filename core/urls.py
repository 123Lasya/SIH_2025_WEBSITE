from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('help/', views.help, name='help'),
    path('faq/', views.faq, name='faq'),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
    path('disclaimer/', views.disclaimer, name='disclaimer'),
    path('contact/', views.contact, name='contact'),
    path("api/mtm-chart/", views.mtm_chart_api, name="mtm_chart_api"),
    path("farmer/mtm-history/", views.farmer_mtm_history, name="farmer_mtm_history"),
    path("buyer/mtm-history/", views.buyer_mtm_history, name="buyer_mtm_history"),
    path("set-language/", views.set_language, name="set_language"),
]
