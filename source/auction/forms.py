from decimal import Decimal
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

from .models import Auction, AuctionUser
        

# Confirmation of auction creation.
        
class AuctionConfirmForm(forms.ModelForm):

    CHOICES = (('yes', _('Yes'),), ('no', _('No'),))
    choice = forms.ChoiceField(widget = forms.RadioSelect, choices = CHOICES, label = _('Are you sure you want to create this auction?'), initial = 'no')
    
    class Meta:
        model = Auction
        fields = ['title', 'item_description', 'price', 'deadline']
        widgets = {
            'title': forms.HiddenInput(),
            'item_description': forms.HiddenInput(),
            'price': forms.HiddenInput(),
            'deadline': forms.HiddenInput(),
        }
        
        
# Bidding.

class BidForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.price = kwargs.pop('price', None)
        super(BidForm, self).__init__(*args, **kwargs)
        self.fields['price'].widget.attrs['min'] = self.price + Decimal('0.01')
        
    class Meta:
        model = Auction
        fields = ['price', 'item_description']
        labels = {'price': 'Bid (€)'}
        widgets = {'item_description': forms.HiddenInput()}
        
        
# Language changing.

class ChangeLanguageForm(forms.Form):
    
    CHOICES = (('en', _('English'),), ('sv', _('Swedish'),))
    language = forms.ChoiceField(widget = forms.RadioSelect, choices = CHOICES, label = _('Please select a language.'))
        

# User registration.

class UserForm(UserCreationForm):

    email = forms.EmailField()
    
    class Meta:
        model = User
        fields = ['username', 'email']
        
    def save(self, commit = True):
        user = super(UserForm, self).save(commit = False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            auction_user = AuctionUser(user = User.objects.get(username = user.username))
            auction_user.save()
        return auction_user