import datetime

from django.db import models
from decimal import Decimal
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.core.validators import MinValueValidator
        

# Field for the auction price.

class PositiveDecimalField(models.DecimalField):
    
    description = 'Positive decimal number'
    
    def formfield(self, **kwargs):
        defaults = {'min_value': Decimal(0)}
        defaults.update(kwargs)
        return super(PositiveDecimalField, self).formfield(**defaults)
        

# Model for auction.

class Auction(models.Model):

    ACTIVE = 0
    BANNED = 1
    ADJUDICATED = 2
    
    STATUS_CHOICES = (
        (ACTIVE, 'Active'),
        (BANNED, 'Banned'),
        (ADJUDICATED, 'Adjudicated'),
    )
    
    status = models.IntegerField(choices = STATUS_CHOICES, default = ACTIVE)

    seller = models.CharField(max_length = 150, verbose_name = _('Seller'))
    title = models.CharField(max_length = 200, verbose_name = _('Title'))
    item_description = models.CharField(max_length = 1000, verbose_name = _('Item description'))
    price = PositiveDecimalField(verbose_name = _('Minimum price (€)'), default = 0, max_digits = 15, decimal_places = 2)
    bidder_pk_string = models.CharField(max_length = 2000)
    last_bidder = models.CharField(max_length = 150)
    deadline = models.DateTimeField(default = datetime.datetime.now())
    locked_by = models.CharField(max_length = 150)
    
    def __str__(self):
        return self.title
        
    def get_absolute_url(self):
        return reverse('detail', kwargs = {'pk': self.pk})
        
    def is_active(self):
        return self.status == self.ACTIVE
        
    def get_bidder_mails(self):
        bidder_pks = self.bidder_pk_string.split(',') if len(self.bidder_pk_string) != 0 else []
        bidder_mails = []
        for pk in bidder_pks:
            bidder_mails.append(User.objects.get(pk = int(pk)).email)
        return bidder_mails
        
    def add_bidder(self, bidder):
        bidder_pks = self.bidder_pk_string.split(',')
        if str(bidder) not in bidder_pks:
            self.bidder_pk_string += str(bidder) if len(self.bidder_pk_string) == 0 else ',' + str(bidder)
            
            
# Model for auction user.

class AuctionUser(models.Model):
    
    LANGUAGE_CHOICES = (
        ('en', 'English'),
        ('sv', 'Swedish'),
    )
    
    language = models.CharField(choices = LANGUAGE_CHOICES, default = 'en', max_length = 2)

    user = models.OneToOneField(User, on_delete = models.CASCADE)
    
    def __str__(self):
        return self.user.username
        
    def get_absolute_url(self):
        return self.user.get_absolute_url()

            
# Model for bid.

class Bid(models.Model):
    
    auction = models.ForeignKey(Auction, on_delete = models.CASCADE)
    bidder = models.CharField(max_length = 150)
    amount = PositiveDecimalField(default = 0, max_digits = 15, decimal_places = 2)
        
    def get_absolute_url(self):
        return reverse('bid_detail_api', kwargs = {'pk': self.pk})