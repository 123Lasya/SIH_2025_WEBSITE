from django.contrib import admin
from .models import FarmerHedge, FarmerContract, Alert

admin.site.register(FarmerHedge)
admin.site.register(FarmerContract)
admin.site.register(Alert)
