from django.db import models
from accounts.models import FarmerProfile
from django.contrib.auth.models import User


# ---------------------------
# 1. HEDGE MODEL
# ---------------------------

class FarmerHedge(models.Model):
    farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE)

    crop = models.CharField(max_length=50)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    hedge_price = models.DecimalField(max_digits=10, decimal_places=2)

    duration_days = models.IntegerField(default=0)
    end_date = models.DateField() 
    # blockchain field
    hedge_hash = models.CharField(max_length=200, blank=True, null=True)
    margin_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    matched_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, default="OPEN")  
    last_mtm_pnl = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    HEDGE_TYPES = [
    ("CALL", "Call"),
    ("PUT", "Put"),
    ]

    hedge_type = models.CharField(max_length=10, choices=HEDGE_TYPES, default="CALL")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Hedge {self.id} - {self.crop}"


# ---------------------------
# 2. CONTRACT MODEL
# ------ ---------------------

class FarmerContract(models.Model):
    farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE)

    crop = models.CharField(max_length=50)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)

    grade_a_price = models.DecimalField(max_digits=10, decimal_places=2)
    grade_b_price = models.DecimalField(max_digits=10, decimal_places=2)
    grade_c_price = models.DecimalField(max_digits=10, decimal_places=2)

    warehouse = models.CharField(max_length=100)

    start_date = models.DateField()
    end_date = models.DateField()

    # ---------- BUYER INFO ----------
    buyer = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    buyer_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('BUYER_ACCEPTED', 'Buyer Accepted'),
            ('FARMER_APPROVED', 'Farmer Approved'),
            ('REJECTED', 'Rejected'),
        ],
        default='PENDING'
    )

    # ---------- CONTRACT STATUS ----------
    contract_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('ACTIVE', 'Active'),
            ('COMPLETED', 'Completed'),
            ('EXPIRED', 'Expired'),
        ],
        default='PENDING'
    )

    blockchain_hash = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


# ---------------------------
# 4. ALERT MODEL
# ---------------------------

# ---------------------------
# 4. ALERT MODEL
# ---------------------------
class Alert(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()

    # Optional link to contract (only for buyer-accepted alerts)
    contract = models.ForeignKey(
        FarmerContract,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Alert for {self.user.username}"


