from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone

from auction.models import Auction, AuctionUser


# Populate database.

class Command(BaseCommand):

    help = 'Populates the database with some example data'

    def handle(self, *args, **options):
        first_id = 0
        for i in range(1, 51):
            User.objects.create_user('user' + str(i), 'user' + str(i) + '@example.com', 'very_easy_password').save()
            auction_user = AuctionUser(user = User.objects.get(username = 'user' + str(i)))
            auction_user.save()
            auction = Auction(seller = auction_user.user.username, title = 'auction' + str(i), item_description = 'Item description.', price = Decimal(0.00), deadline = timezone.now() + timedelta(days = 30))
            auction.save()
            if i == 1:
                first_id = auction.id
        for i in range(0, 10):
            auction = Auction.objects.get(pk = first_id + i)
            auction.price += Decimal('0.01')
            user = User.objects.get(username = 'user' + str(i + 2))
            auction.add_bidder(user.pk)
            auction.last_bidder = user.username
            auction.save()