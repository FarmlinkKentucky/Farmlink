from django import forms
from .models import Listing

class ListingEditForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ['title', 'imageUrl', 'price', 'quantity_available_lbs', 'address', 'available_until_date', 'category']
