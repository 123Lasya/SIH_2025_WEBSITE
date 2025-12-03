from django.contrib import admin
from .models import (
    FarmerAadhaarKYC,
    FarmerProfile,
    BuyerBusinessProfile,
    BuyerTraderProfile,
    BankDetail,
)

admin.site.register(FarmerAadhaarKYC)
admin.site.register(FarmerProfile)
admin.site.register(BuyerBusinessProfile)
admin.site.register(BuyerTraderProfile)
admin.site.register(BankDetail)
