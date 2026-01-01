from django.db import models
from django.contrib.auth.models import User

class BuyerHedge(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE)

    crop = models.CharField(max_length=50)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    hedge_price = models.DecimalField(max_digits=10, decimal_places=2)
    margin_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    matched_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, default="OPEN")  
    last_mtm_pnl = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    end_date = models.DateField()

    hedge_hash = models.CharField(max_length=200, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    HEDGE_TYPES = [
    ("CALL", "Call"),
    ("PUT", "Put"),
    ]

    hedge_type = models.CharField(max_length=10, choices=HEDGE_TYPES, default="CALL")

    def __str__(self):
        return f"Buyer Hedge {self.id} - {self.crop}"
