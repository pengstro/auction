from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from auction.models import Auction


# Custom command for periodically making sure that due auctions are resolved.

class Command(BaseCommand):

    help = 'Resolves auctions that are due'
    
    def handle(self, *args, **options):
        auctions = Auction.objects.all()
        for auction in auctions:
            if auction.deadline < timezone.now() and auction.status == Auction.ACTIVE:
                auction.status = Auction.ADJUDICATED
                auction.save()
                if auction.last_bidder == '':
                    send_mail('Auction resolved', 'Auction ' + auction.title + ' has been resolved. There were no bids.', 'pengstro@abo.fi', [User.objects.get(username = auction.seller).email])
                else:
                    send_mail('Auction resolved', 'Auction ' + auction.title + ' has been resolved. The winner is ' + auction.last_bidder + '.', 'pengstro@abo.fi', auction.get_bidder_mails())