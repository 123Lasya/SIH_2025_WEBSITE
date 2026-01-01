from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal


class MTMHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    hedge_type = models.CharField(max_length=20)  # FARMER or BUYER
    hedge_id = models.IntegerField()

    date = models.DateField()

    crop = models.CharField(max_length=50)

    quantity = models.DecimalField(max_digits=14, decimal_places=2)

    hedge_price = models.DecimalField(max_digits=14, decimal_places=2)
    market_price = models.DecimalField(max_digits=14, decimal_places=2)

    pnl = models.DecimalField(max_digits=14, decimal_places=2)

    wallet_balance_after = models.DecimalField(max_digits=14, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} | {self.crop} | {self.date} | {self.pnl}"

from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class MTMRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    hedge_type = models.CharField(max_length=20, default="FARMER")   # Default to FARMER

    # Hedge ID reference
    hedge_id = models.IntegerField(default=0)

    date = models.DateField()

    crop = models.CharField(max_length=50)
    hedge_price = models.DecimalField(max_digits=10, decimal_places=2)
    market_price = models.DecimalField(max_digits=10, decimal_places=2)

    quantity = models.DecimalField(max_digits=12, decimal_places=2)

    pnl = models.DecimalField(max_digits=12, decimal_places=2)
    wallet_balance_after = models.DecimalField(max_digits=14, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.crop} - {self.date}"
