from django.db import models
from django.contrib.auth.models import User

class BuyerHedge(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE)

    crop = models.CharField(max_length=50)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    hedge_price = models.DecimalField(max_digits=10, decimal_places=2)

    end_date = models.DateField()

    hedge_hash = models.CharField(max_length=200, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Buyer Hedge {self.id} - {self.crop}"
