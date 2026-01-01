from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver


# 1) Dummy Aadhaar KYC table for farmers
class FarmerAadhaarKYC(models.Model):
    aadhaar_number = models.CharField(max_length=12, unique=True)
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.aadhaar_number} - {self.email}"


# 2) Farmer Profile
import uuid

class FarmerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    farmer_uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    aadhaar_number = models.CharField(max_length=12)
    mobile = models.CharField(max_length=15)
    alternate_mobile = models.CharField(max_length=15, blank=True, null=True)

    village = models.CharField(max_length=100)
    mandal = models.CharField(max_length=100)
    district = models.CharField(max_length=100)

    land_size = models.CharField(max_length=50)

    grows_groundnut = models.BooleanField(default=False)
    grows_soybean = models.BooleanField(default=False)
    grows_sunflower = models.BooleanField(default=False)

    def __str__(self):
        return f"Farmer: {self.user.username}"



# 3) Business Buyer Profile
class BuyerBusinessProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    buyer_uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    company_name = models.CharField(max_length=200)
    company_type = models.CharField(max_length=50)
    gst_number = models.CharField(max_length=50)

    business_email = models.EmailField()
    business_phone = models.CharField(max_length=15)

    factory_address = models.CharField(max_length=255)
    intake_capacity = models.CharField(max_length=100)

    prefers_groundnut = models.BooleanField(default=False)
    prefers_soybean = models.BooleanField(default=False)
    prefers_sunflower = models.BooleanField(default=False)

    def __str__(self):
        return f"Business Buyer: {self.user.username}"

# 4) Trader Buyer Profile
import uuid

class BuyerTraderProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    buyer_uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    district = models.CharField(max_length=255,default='Guntur')
    trader_type = models.CharField(max_length=50)
    shop_name = models.CharField(max_length=200)
    license_number = models.CharField(max_length=100)
    capacity = models.CharField(max_length=100)

    prefers_groundnut = models.BooleanField(default=False)
    prefers_soybean = models.BooleanField(default=False)
    prefers_sunflower = models.BooleanField(default=False)

    def __str__(self):
        return f"Trader Buyer: {self.user.username}"



# 5) Bank Details (common for farmer + buyer)
class BankDetail(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    account_holder_name = models.CharField(max_length=200)
    bank_name = models.CharField(max_length=200)
    account_number = models.CharField(max_length=50)
    ifsc_code = models.CharField(max_length=20)
    upi_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Bank: {self.user.username} - {self.account_number}"
    

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="wallet")
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    locked_margin = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    def __str__(self):
        return f"Wallet({self.user.username})"

    @property
    def available_balance(self):
        return self.balance - self.locked_margin


@receiver(post_save, sender=User)
def create_wallet_for_user(sender, instance, created, **kwargs):
    """
    Automatically create a Wallet whenever a new User is created.
    """
    if created:
        Wallet.objects.create(user=instance)
