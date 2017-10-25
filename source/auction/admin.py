from django.contrib import admin

from .models import Auction, AuctionUser

admin.site.register(Auction)
admin.site.register(AuctionUser)