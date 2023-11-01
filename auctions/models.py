from django.contrib.auth.models import AbstractUser
from django.db import models
import datetime

class User(AbstractUser):
    pass

class Category(models.Model):
    categoryName = models.CharField(max_length=50)

    def __str__(self):
        return self.categoryName


class Listing(models.Model):
    title = models.CharField(max_length=30)
    imageUrl = models.CharField(max_length=1000)
    price = models.DecimalField(max_digits=10, decimal_places=2) 
    address = models.CharField(max_length=300)
    isActive = models.BooleanField(default=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name="user")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, blank=True, null=True, related_name="category")
    available_until_date = models.DateField(null=True, blank=True)  
    quantity_available_lbs = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)  
    total_quantity_lbs = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)  
    watchlist = models.ManyToManyField(User, blank=True, related_name="listingWatchlist")
    created_at = models.DateField(default=datetime.date.today())  

    def __str__(self):
        return self.title

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)  
    pickup_date = models.DateField(null=True, blank=True) 
    pickup_time = models.TimeField()
    pickup_person = models.CharField(max_length=255)
    email = models.EmailField()
    phone_number = models.CharField(max_length=12)
    payment_method = models.CharField(max_length=255, choices=[("pay_on_site", "Pay on Site")])
    order_date = models.DateTimeField(auto_now_add=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return f"Order for {self.listing.title} by {self.user.username}"
