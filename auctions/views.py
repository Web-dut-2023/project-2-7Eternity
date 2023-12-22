from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from .forms import ListingForm
from .models import User, Listing, Comment, Bid

from django.db.models import Max


def index(request):
    active_listings = Listing.objects.filter(active=True)  # 获取所有当前活跃的拍卖列表
    return render(request, "auctions/index.html", {"listings": active_listings})


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

@login_required
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

@login_required
def watchlist(request):
    user = request.user
    listings = user.watchlist.all()
    return render(request, "auctions/watchlist.html", {
        "listings": listings
    })

@login_required
def add_watchlist(request, listing_id):
    user = request.user
    listing = get_object_or_404(Listing, pk=listing_id, active=True)
    user.watchlist.add(listing)
    messages.success(request, "Listing added to watchlist.")
    return redirect("listing_detail", listing_id=listing.id)

@login_required
def remove_watchlist(request, listing_id):
    user = request.user
    listing = get_object_or_404(Listing, pk=listing_id, active=True)
    user.watchlist.remove(listing)
    messages.success(request, "Listing removed from watchlist.")
    return redirect("listing_detail", listing_id=listing.id)

def listing_detail(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id, active=True)
    bids = Bid.objects.filter(listing=listing).order_by("-amount")
    comments = Comment.objects.filter(listing=listing).order_by("-created_at")
    watchlisted = False
    if request.user.is_authenticated:
        user = request.user
        watchlisted = user.watchlist.filter(pk=listing_id).exists()
    return render(request, "auctions/listing_detail.html", {
        "listing": listing,
        "bids": bids,
        "comments": comments,
        "watchlisted": watchlisted
    })

# @login_required
# def bid(request, listing_id):
#     listing = get_object_or_404(Listing, pk=listing_id, active=True)
#     user = request.user
#     amount = float(request.POST["amount"])
#     if amount <= listing.current_price:
#         messages.error(request, "Bid must be higher than current price.")
#         return redirect("listing_detail", listing_id=listing.id)
#     if user == listing.creator:
#         messages.error(request, "You cannot bid on your own listing.")
#         return redirect("listing_detail", listing_id=listing.id)
#     if listing.current_winner and user == listing.current_winner:
#         listing.current_bid.amount = amount
#         listing.current_bid.save()
#         messages.success(request, "Your bid has been updated.")
#     else:
#         bid = Bid(listing=listing, bidder=user, amount=amount)
#         bid.save()
#         listing.current_bid = bid
#         listing.current_price = bid.amount
#         listing.current_winner = user
#         listing.save()
#         messages.success(request, "Your bid has been placed.")
#     return redirect("listing_detail", listing_id=listing.id)

@login_required
def bid(request, listing_id):
    if request.method == "POST":
        bid_amount = float(request.POST["bid_amount"])
        listing = get_object_or_404(Listing, pk=listing_id)
        current_price = float(listing.current_price)
        if bid_amount < current_price or (listing.bids.aggregate(Max('amount'))['amount__max'] or 0) >= bid_amount:
            messages.error(request, "Invalid bid amount.")
            return redirect("listing_detail", listing_id=listing.id)
        else:
            Bid.objects.create(listing=listing, bidder=request.user, amount=bid_amount)
            listing.current_price = bid_amount
            listing.current_winner = request.user
            listing.save()
            messages.success(request, "Bid placed successfully!")
            return redirect("listing_detail", listing_id=listing.id)
    else:
        return redirect("index")
@login_required
def comment(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id, active=True)
    user = request.user
    content = request.POST["comment_content"]
    comment = Comment(listing=listing, commenter=user, content=content)
    comment.save()
    messages.success(request, "Your comment has been added.")
    return redirect("listing_detail", listing_id=listing.id)

@login_required
def create_listing(request):
    if request.method == "POST":
        title = request.POST["title"]
        description = request.POST["description"]
        starting_bid = float(request.POST["starting_bid"])
        image_url = request.POST["image_url"]
        category = request.POST["category"]
        creator = request.user
        listing = Listing(
            title=title,
            description=description,
            starting_bid=starting_bid,
            image_url=image_url,
            category=category,
            creator=creator
        )
        listing.save()
        messages.success(request, "Listing created.")
        return redirect("listing_detail", listing_id=listing.id)
    return render(request, "auctions/create_listing.html")

@login_required
def close_listing(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id, active=True, creator=request.user)
    listing.active = False
    listing.save()
    # award the item to the current winner
    if listing.current_winner:
        messages.success(request, f"{listing.title} has been sold to {listing.current_winner.username} for ${listing.current_price:.2f}.")
    else:
        messages.success(request, f"{listing.title} has been closed with no bids.")
    return redirect('index')



def category_list(request):
    categories = Listing.objects.values_list('category', flat=True).distinct()
    return render(request, 'auctions/category_list.html', {'categories': categories})

def category_listings(request, category):
    listings = Listing.objects.filter(category=category, active=True)
    return render(request, 'auctions/category_listings.html', {'listings': listings})



