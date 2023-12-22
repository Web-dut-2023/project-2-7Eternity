from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("watchlist/", views.watchlist, name="watchlist"),
    path("add_watchlist/<int:listing_id>/", views.add_watchlist, name="add_watchlist"),
    path("remove_watchlist/<int:listing_id>/", views.remove_watchlist, name="remove_watchlist"),
    path("listing_detail/<int:listing_id>/", views.listing_detail, name="listing_detail"),
    path("bid/<int:listing_id>/", views.bid, name="bid"),
    path("comment/<int:listing_id>/", views.comment, name="comment"),
    path("create_listing/", views.create_listing, name="create_listing"),
    path("close_listing/<int:listing_id>/", views.close_listing, name="close_listing"),
    path('categories/', views.category_list, name='category_list'),
    path('category/<str:category>/', views.category_listings, name='category'),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register")
]
