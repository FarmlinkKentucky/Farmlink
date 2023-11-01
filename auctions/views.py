from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from .models import User, Category, Listing, Order
from django.shortcuts import render, HttpResponseRedirect, get_object_or_404, HttpResponse, redirect
from .models import Order, Listing, Category
from decimal import Decimal
from django.contrib import messages
from datetime import date, datetime
from django.core.exceptions import ValidationError
import datetime as dt
from .forms import ListingEditForm

KENTUCKY_TAX_RATE = 0.06  # 6% tax rate for Kentucky

def terms(request):
   return render(request, "auctions/terms.html")

def edit_listing(request, id):
    listing = get_object_or_404(Listing, pk=id)

    # Check if the user is the owner of the listing
    if request.user != listing.owner:
        return redirect('listing', id=id)

    if request.method == 'POST':
        form = ListingEditForm(request.POST, instance=listing)
        if form.is_valid():
            form.save()
            return redirect('listing', id=id)
    else:
        form = ListingEditForm(instance=listing)

    return render(request, 'auctions/editListing.html', {
        'form': form,
        'listing': listing,
    })

def delete_listing(request, id):
    listing = get_object_or_404(Listing, pk=id)
    if request.method == 'POST' and request.user == listing.owner:
        listing.delete()
        return HttpResponseRedirect(reverse('shop'))
    return redirect('listing', id=id)

def delete_order(request, id):
    order = get_object_or_404(Order, pk=id)
    
    # Check if the user is the owner of the associated listing or an admin
    if request.user == order.user or request.user == order.listing.owner or request.user.is_staff:
        # Increase the available quantity by the quantity in the order
        order.listing.quantity_available_lbs += order.quantity
        
        # Set the listing as active since it has available quantity now
        order.listing.isActive = True
        
        order.listing.save()
        
        order.delete()
        messages.success(request, "Order has been canceled successfully.")
    else:
        messages.error(request, "You do not have permission to cancel this order.")

    return redirect('owner_orders')

def owner_orders(request):
    user = request.user
    seller_orders = Order.objects.filter(listing__owner=user)
    user_orders = Order.objects.filter(user=user)
    return render(request, "auctions/orders.html", {
        "seller_orders": seller_orders,
        "user_orders": user_orders
    })

def listing(request, id):
    listingData = Listing.objects.get(pk=id)
    isListingInWatchlist = request.user in listingData.watchlist.all()
    return render(request, "auctions/listing.html", {
        "listing": listingData,
        "isListingInWatchlist": isListingInWatchlist
    })

def displayWatchlist(request):
    currentUser = request.user
    listings = currentUser.listingWatchlist.all()

    return render(request, "auctions/watchlist.html", {
        "listings": listings
    })

def removeWatchlist(request, id):
    listingData = Listing.objects.get(pk=id)
    currentUser = request.user
    listingData.watchlist.remove(currentUser)
    return HttpResponseRedirect(reverse("listing", args=[id, ]))

def addWatchlist(request, id):
    listingData = Listing.objects.get(pk=id)
    currentUser = request.user
    listingData.watchlist.add(currentUser)
    return HttpResponseRedirect(reverse("listing", args=[id, ]))

def index(request):
    return render(request, "auctions/index.html")

def shop(request):
    activeListings = Listing.objects.filter(isActive=True)

    today = date.today()
    expired_listings = activeListings.filter(available_until_date__lt=today)
    expired_listings.update(isActive=False)

    allCategories = Category.objects.all()
    
    return render(request, "auctions/shop.html", {
        "listings": activeListings,
        "categories": allCategories
    })

def about(request):
    return render(request, "auctions/about.html")

def reviews(request):
    return render(request, "auctions/reviews.html")

def purchase_form(request, id):
    listing = get_object_or_404(Listing, pk=id)
    return render(request, "auctions/purchase.html", {
        "listing": listing,
        "form": Order(),
        "available_quantity": listing.quantity_available_lbs
    })

def purchase(request, id):
    if request.method == "POST":
        user = request.user
        listing = get_object_or_404(Listing, pk=id)

        if user == listing.owner:
            messages.error(request, "You cannot order your own product.")
            return redirect('listing', id=id)
        
        quantity_ordered = Decimal(request.POST["quantity"])  # Convert to Decimal
        available_quantity = listing.quantity_available_lbs

        if quantity_ordered < Decimal('0.00'):
            messages.error(request, "Quantity must be non-negative.")
            return redirect('purchase_form', id=id)
        
        if quantity_ordered > available_quantity:
            messages.error(request, "Quantity ordered exceeds available quantity.")
            return redirect('purchase_form', id=id)

        pickup_time = request.POST["pickup_time"]
        pickup_person = request.POST["pickup_person"]
        email = request.POST["email"]
        phone_number = request.POST["phone_number"]

        # Check if the pickup date is within the allowed range
        pickup_date_str = request.POST["pickup_date"]
        listing_creation_date = listing.created_at.date()
        available_until_date_str = listing.available_until_date.strftime("%Y-%m-%d")

        try:
            pickup_date = datetime.strptime(pickup_date_str, "%Y-%m-%d").date()
            available_until_date = datetime.strptime(available_until_date_str, "%Y-%m-%d").date()

            # Allow pickup date on or before the available until date
            if pickup_date < listing_creation_date or pickup_date > available_until_date:
                messages.error(request, "Pickup date must be on or before the available until date.")
                return redirect('purchase_form', id=id)

        
        except ValueError:
            messages.error(request, "Invalid date or time format.")
            return redirect('purchase_form', id=id)

        # Calculate the updated price based on the quantity ordered
        updated_price = Decimal(str((quantity_ordered / available_quantity) * listing.price))

        # Calculate the tax amount based on the updated price and tax rate
        tax_amount = updated_price * Decimal(KENTUCKY_TAX_RATE)

        # Add the tax to the updated price
        updated_price += tax_amount

        updated_price = round(updated_price, 2)

        order = Order(  
            user=user,
            listing=listing,
            quantity=quantity_ordered,
            pickup_date=pickup_date,
            pickup_time=pickup_time,
            pickup_person=pickup_person,
            email=email,
            phone_number=phone_number,
            price=updated_price
        )

        order.save()

        # Update the available quantity of the listing
        listing.quantity_available_lbs -= quantity_ordered

        # Check if the available quantity is zero, and if so, mark the listing as inactive
        if listing.quantity_available_lbs <= 0:
            listing.isActive = False

        listing.save()
        messages.success(request, "Order placed successfully.")
        return HttpResponseRedirect(reverse('index'))

def displayCategory(request):
    if request.method == "POST":
        categoryFromForm = request.POST['category']
        category = Category.objects.get(categoryName = categoryFromForm)
        activeListings = Listing.objects.filter(isActive=True, category=category)
        allCategories = Category.objects.all()
        return render(request, "auctions/shop.html", {
            "listings":activeListings,
            "categories":allCategories
            }) 

def createListing(request):
    if request.method == "GET":
        allCategories = Category.objects.all()
        return render(request, "auctions/create.html", {
            "categories": allCategories
        })
    
    else:
        title = request.POST["title"]
        imageurl = request.POST["imageurl"]
        price = Decimal(request.POST["price"])
        quantity_available_lbs = Decimal(request.POST["quantity_available_lbs"])
        total_quantity_lbs=Decimal(request.POST["quantity_available_lbs"])
        address = request.POST["address"]
        available_until_date = request.POST["available_until_date"]
        category = request.POST["category"]
        currentUser = request.user
        categoryData = Category.objects.get(categoryName=category)
        created_at = dt.date.today()

        # Check for negative price and quantity
        if price < Decimal('0.00') or quantity_available_lbs < Decimal('0.00'):
            messages.error(request, "Price and quantity must be non-negative.")
            return HttpResponseRedirect(reverse('create'))
        
       
        if (datetime.strptime(available_until_date, "%Y-%m-%d").date()) < created_at:
            messages.error(request, "Available until date cannot be less than today's date")
            return HttpResponseRedirect(reverse('create'))

        newListing = Listing(
            title=title,
            imageUrl=imageurl,
            price=price,
            quantity_available_lbs=quantity_available_lbs,
            total_quantity_lbs=total_quantity_lbs,
            address=address,
            available_until_date=available_until_date,
            created_at=created_at,
            category=categoryData,
            owner=currentUser
        )

        try:
            newListing.full_clean()  # Validate the model fields
            newListing.save()
            messages.success(request, "Listing created successfully.")
            return HttpResponseRedirect(reverse(index))
        except ValidationError as e:
            messages.error(request, "Validation error: " + str(e))
            return HttpResponseRedirect(reverse('create'))

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))

def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
    