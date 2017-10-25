import base64
import json
import time
import urllib.request
from datetime import timedelta
from decimal import Decimal
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import views as auth_views
from django.core.mail import send_mail
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.utils import timezone, translation
from django.utils.decorators import method_decorator
from django.views import generic, View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.edit import FormView, CreateView, UpdateView

from .models import Auction, Bid
from .forms import UserForm, AuctionConfirmForm, BidForm, ChangeLanguageForm


# Home page. Contains a list of all auctions.

class AuctionListView(generic.ListView):

    model = Auction
        

# Results of a search for auctions.
        
class SearchView(generic.ListView):
    
    model = Auction
    template_name = 'auction/search.html'
    
    def get_queryset(self):
        return Auction.objects.filter(title__icontains = self.request.GET['search'])
        

# Details of specified auction.
        
class AuctionDetailView(generic.DetailView):

    model = Auction
    
    def dispatch(self, *args, **kwargs):
        if not self.request.user.is_staff and not self.get_object().is_active():
            raise PermissionDenied
        return super(AuctionDetailView, self).dispatch(*args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super(AuctionDetailView, self).get_context_data(**kwargs)
        context['is_seller'] = context['auction'].seller == self.request.user.username
        response = urllib.request.urlopen('https://openexchangerates.org/api/latest.json?app_id=52a1bd80785b4cc7896a137d206b5ce0')
        content = response.read()
        data = json.loads(content)
        rate = 1 / float(data['rates']['EUR'])
        usd = float(context['auction'].price) * rate
        context['currencies'] = {}
        for key in data['rates'].keys():
            context['currencies'][key] = format(usd * float(data['rates'][key]), '.2f')
        context['is_active'] = context['auction'].is_active()
        return context
    
    
# Links to editing user information.
    
@method_decorator(login_required, name = 'dispatch')
class EditUserView(generic.TemplateView):

    template_name = 'registration/edit_user.html'
    

# Form for editing user email address.
    
@method_decorator(login_required, name = 'dispatch')
class EditEmailView(UpdateView):

    model = User
    fields = ['email']
    success_url = reverse_lazy('auction:edit_email_done')
    template_name = 'registration/edit_email.html'
    
    def get_object(self, queryset = None):
        return self.request.user
        

# Success page for email edit.
        
@method_decorator(login_required, name = 'dispatch')
class EditEmailDoneView(generic.TemplateView):

    template_name = 'registration/edit_email_done.html'
    

# Form for creating new auction. Forwards the data to the confirmation form.

@method_decorator(login_required, name = 'dispatch')
class NewAuctionView(CreateView):

    model = Auction
    fields = ['title', 'item_description', 'price', 'deadline']
    
    def form_valid(self, form):
        if form.cleaned_data['deadline'] < timezone.now() + timedelta(days = 3):
            form.instance.deadline = timezone.now() + timedelta(days = 3)
        confirm_form = AuctionConfirmForm(instance = form.instance)
        return render(self.request, 'auction/auction_confirm.html', {'form': confirm_form})
    
    
# Form prompting the user for confirmation about creating the new auction. Contains the auction data as hidden inputs.

@method_decorator(login_required, name = 'dispatch')
class NewAuctionConfirmView(View):
    
    def get(self, request):
        return HttpResponseRedirect(reverse('auction:new_auction'))
        
    def post(self, request):
        form = AuctionConfirmForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['choice'] == 'no':
                return HttpResponseRedirect(reverse('index'))
            auction = Auction(
                seller = request.user.username,
                title = form.cleaned_data['title'],
                item_description = form.cleaned_data['item_description'],
                price = form.cleaned_data['price'],
                deadline = form.cleaned_data['deadline'] if form.cleaned_data['deadline'] >= timezone.now() + timedelta(days = 3) else timezone.now() + timedelta(days = 3)
            )
            auction.save()
            send_mail('Auction created', 'Your auction was successfully created. Link to auction details: https://pengstro.pythonanywhere.com/auction/' + str(auction.pk), 'pengstro@abo.fi', [request.user.email])
            return HttpResponseRedirect(reverse('index'))
            

# Form for editing the item description of a given auction.
            
@method_decorator(login_required, name = 'dispatch')
class EditDescriptionView(UpdateView):
    
    model = Auction
    fields = ['item_description']
    template_name = 'auction/edit_description.html'
    
    def dispatch(self, *args, **kwargs):
        if self.get_object().seller != self.request.user.username or not self.get_object().is_active():
            raise PermissionDenied
        return super(EditDescriptionView, self).dispatch(*args, **kwargs)
        
    def form_valid(self, form):
        auction = form.instance
        if not auction.is_active():
            raise PermissionDenied
        while auction.locked_by != '' and auction.locked_by != self.request.user.username:
            time.sleep(1)
        auction.locked_by = self.request.user.username
        auction.save()
        redirect = super(EditDescriptionView, self).form_valid(form)
        auction.locked_by = ''
        auction.save()
        return redirect
        
# Form for bidding on auction.

@method_decorator(login_required, name = 'dispatch')
class BidView(UpdateView):

    model = Auction
    form_class = BidForm
    template_name = 'auction/bid.html'
    
    def dispatch(self, *args, **kwargs):
        auction = self.get_object()
        if auction.seller == self.request.user.username or not auction.is_active():
            raise PermissionDenied
        return super(BidView, self).dispatch(*args, **kwargs)
        
    def get_form_kwargs(self):
        kwargs = super(BidView, self).get_form_kwargs()
        kwargs['price'] = self.get_object().price
        return kwargs
        
    def form_valid(self, form):
        auction = Auction.objects.get(pk = form.instance.id)
        if not auction.is_active():
            raise PermissionDenied
        while auction.locked_by != '' and auction.locked_by != self.request.user.username:
            time.sleep(1)
        auction.locked_by = self.request.user.username
        auction.save()
        if auction.item_description != form.cleaned_data['item_description']:
            auction.locked_by = ''
            auction.save()
            return render(self.request, 'auction/description_changed.html')
        if auction.price >= form.cleaned_data['price']:
            auction.locked_by = ''
            auction.save()
            return render(self.request, 'auction/outbid.html')
        bid(auction, form.cleaned_data['price'], self.request.user)
        auction.locked_by = ''
        auction.save()
        return HttpResponseRedirect(reverse('detail', kwargs = {'pk': form.instance.id}))
            
            
# View for auction ban.
        
@method_decorator(login_required, name = 'dispatch')
class BanView(generic.TemplateView):

    template_name = 'auction/ban.html'
    
    def dispatch(self, *args, **kwargs):
        auction = Auction.objects.get(pk = kwargs['pk'])
        if not self.request.user.is_staff or not auction.is_active():
            raise PermissionDenied
        auction.status = Auction.BANNED
        auction.save()
        recipients = [User.objects.get(username = auction.seller).email]
        recipients.extend(auction.get_bidder_mails())
        send_mail('Auction banned', 'Auction ' + auction.title + ' has been banned.', 'pengstro@abo.fi', recipients)
        return super(BanView, self).dispatch(*args, **kwargs)
        
    
# Form for registering new user.
      
class RegisterView(CreateView):

    model = User
    form_class = UserForm
    

# Success page for user registration.
    
class RegisterDoneView(generic.TemplateView):

    template_name = 'registration/register_done.html'
    
    
# Browse/search via API.

class AuctionListAPIView(View):
    
    def get(self, request):
        try:
            auctions = Auction.objects.filter(title__icontains = request.GET['title'])
        except KeyError:
            auctions = Auction.objects.all()
        data = []
        for auction in auctions:
            if auction.is_active():
                data.append({})
                index = len(data) - 1
                data[index]['id'] = str(auction.id)
                data[index]['title'] = auction.title
                data[index]['seller'] = auction.seller
                data[index]['item_description'] = auction.item_description
                data[index]['highest_bid'] = auction.price
                data[index]['deadline'] = auction.deadline
        return JsonResponse({'data': data})
        
        
# View auction details via API.

class AuctionDetailAPIView(View):

    def get(self, request, pk):
        try:
            auction = Auction.objects.get(pk = pk)
        except Auction.DoesNotExist:
            return JsonResponse({'detail': 'No auction with the given ID exists'}, status = 404)
        if not auction.is_active():
            return JsonResponse({'detail': 'This auction is no longer active'}, status = 403)
        data = {}
        data['id'] = str(auction.id)
        data['title'] = auction.title
        data['seller'] = auction.seller
        data['item_description'] = auction.item_description
        data['highest_bid'] = auction.price
        data['deadline'] = auction.deadline
        return JsonResponse({'data': data})
        
        
# Bid via API.

@method_decorator(csrf_exempt, name = 'dispatch')
class BidAPIView(View):
    
    def post(self, request):
        try:
            auth_header = request.META['HTTP_AUTHORIZATION']
        except KeyError:
            return JsonResponse({'detail': 'No credentials given'}, status = 401)
        encoded_credentials = auth_header.split(' ')[1]
        decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8").split(':')
        username = decoded_credentials[0]
        password = decoded_credentials[1]
        user = authenticate(username = username, password = password)
        if user is None:
            return JsonResponse({'detail': 'Incorrect username or password'}, status = 401)
        body_unicode = request.body.decode('utf-8')
        try:
            data = json.loads(body_unicode)
        except json.JSONDecodeError:
            return JsonResponse({'detail': 'JSON wrongly formatted'}, status = 400)
        if 'auction_id' not in data:
            return JsonResponse({'detail': 'Auction ID not given'}, status = 400)
        if 'bid' not in data:
            return JsonResponse({'detail': 'Bid amount not given'}, status = 400)
        try:
            auction = Auction.objects.get(pk = data['auction_id'])
        except Auction.DoesNotExist:
            return JsonResponse({'detail': 'No auction with the given ID exists'}, status = 404)
        if not auction.is_active():
            return JsonResponse({'detail': 'This auction is no longer active'}, status = 403)
        if auction.seller == user.username:
            return JsonResponse({'detail': 'You cannot bid on your own auction'}, status = 403)
        amount = Decimal(data['bid'])
        while auction.locked_by != '' and auction.locked_by != username:
            time.sleep(1)
        auction.locked_by = username
        auction.save()
        if amount < auction.price + Decimal('0.01'):
            return JsonResponse({'detail': 'Bid must be greater than previous bid'}, status = 400)
        bid_object = bid(auction, amount, user)
        auction.locked_by = ''
        auction.save()
        response = JsonResponse({'data': {'id': str(bid_object.id), 'auction_id': str(bid_object.auction.id), 'bidder': bid_object.bidder, 'amount': str(bid_object.amount)}}, status = 201)
        response['Location'] = request.build_absolute_uri(bid_object.get_absolute_url())
        return response
        
        
# View bid details via API.

class BidDetailAPIView(View):

    def get(self, request, pk):
        try:
            auth_header = request.META['HTTP_AUTHORIZATION']
        except KeyError:
            return JsonResponse({'detail': 'No credentials given'}, status = 401)
        encoded_credentials = auth_header.split(' ')[1]
        decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8").split(':')
        username = decoded_credentials[0]
        password = decoded_credentials[1]
        user = authenticate(username = username, password = password)
        if user is None:
            return JsonResponse({'detail': 'Incorrect username or password'}, status = 401)
        bid = Bid.objects.get(pk = pk)
        if user.username != bid.bidder:
            return JsonResponse({'detail': 'You cannot view another user\'s bid'}, status = 403)
        data = {}
        data['id'] = str(pk)
        data['auction_id'] = str(bid.auction.id)
        data['bidder'] = bid.bidder
        data['amount'] = str(bid.amount)
        return JsonResponse({'data': data})
        
        
# Form for changing language.

class ChangeLanguageView(FormView):

    form_class = ChangeLanguageForm
    template_name = 'auction/change_language.html'
    success_url = reverse_lazy('index')
    
    def form_valid(self, form):
        translation.activate(form.cleaned_data['language'])
        self.request.session[translation.LANGUAGE_SESSION_KEY] = form.cleaned_data['language']
        if self.request.user.is_authenticated:
            self.request.user.auctionuser.language = form.cleaned_data['language']
            self.request.user.auctionuser.save()
        return super(ChangeLanguageView, self).form_valid(form)
        
        
# Form for logging in.

class LoginView(auth_views.LoginView):

    def form_valid(self, form):
        language = form.get_user().auctionuser.language
        translation.activate(language)
        self.request.session[translation.LANGUAGE_SESSION_KEY] = language
        return super(LoginView, self).form_valid(form)
        
        
# Bidding.

def bid(auction, amount, bidder):
    seller = User.objects.get(username = auction.seller)
    recipients = [seller.email, bidder.email] if auction.last_bidder == '' or auction.last_bidder == bidder.username else [seller.email, bidder.email, User.objects.get(username = auction.last_bidder).email]
    send_mail('Bid registered', 'A new bid has been registered for auction ' + auction.title + '.', 'pengstro@abo.fi', recipients)
    auction.price = amount
    auction.add_bidder(bidder.pk)
    auction.last_bidder = bidder.username
    if auction.deadline - timezone.now() < timedelta(minutes = 5):
        auction.deadline += timedelta(minutes = 5)
    auction.save()
    bid = Bid(auction = auction, bidder = bidder.username, amount = amount)
    bid.save()
    return bid