from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("about", views.about, name="about"),
    path("shop", views.shop, name="shop"),
    path("reviews", views.reviews, name="reviews"),
    path("terms", views.terms, name="terms"),
    path("create", views.createListing, name="create"),
    path("purchase_form/<int:id>", views.purchase_form, name="purchase_form"),
    path("purchase/<int:id>", views.purchase, name="purchase"),
    path("displayCategory", views.displayCategory, name="displayCategory"),
    path("listing/<int:id>", views.listing, name="listing"),
    path("removeWatchlist/<int:id>", views.removeWatchlist, name="removeWatchlist"),
    path("addWatchlist/<int:id>", views.addWatchlist, name="addWatchlist"),
    path("watchlist", views.displayWatchlist, name="watchlist"),
    path("owner_orders", views.owner_orders, name="owner_orders"),
    path('delete_order/<int:id>/', views.delete_order, name='delete_order'),
    path('listing/<int:id>/delete/', views.delete_listing, name='delete_listing'),
    path('listing/<int:id>/edit/', views.edit_listing, name='edit_listing'),
]
