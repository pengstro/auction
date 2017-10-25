import pytz
from datetime import timedelta
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Auction
from .views import NewAuctionView


class CreateAuctionTests(TestCase):

    def test_unauthenticated_user(self):
        """
        Unauthenticated users are redirected to login page.
        """
        response = self.client.get(reverse('auction:new_auction'))
        self.assertEqual(response.status_code, 302)
        
    def test_authenticated_user(self):
        """
        Authenticated users are granted access.
        """
        User.objects.create_user('user1', 'user1@example.com', 'very_easy_password')
        self.client.login(username = 'user1', password = 'very_easy_password')
        response = self.client.get(reverse('auction:new_auction'))
        self.assertEqual(response.status_code, 200)
        
    def test_wrongly_formatted_price(self):
        """
        A wrongly formatted price is rejected.
        """
        User.objects.create_user('user1', 'user1@example.com', 'very_easy_password')
        self.client.login(username = 'user1', password = 'very_easy_password')
        response = self.client.post(reverse('auction:new_auction'), {'title': 'Auction title', 'item_description': 'Item description', 'price': 'one gazillion euros', 'deadline': timezone.now().strftime("%Y-%m-%d %H:%M:%S")})
        self.assertContains(response, 'Enter a number.')

    def test_negative_min_price(self):
        """
        A negative minimum price is rejected.
        """
        User.objects.create_user('user1', 'user1@example.com', 'very_easy_password')
        self.client.login(username = 'user1', password = 'very_easy_password')
        response = self.client.post(reverse('auction:new_auction'), {'title': 'Auction title', 'item_description': 'Item description', 'price': Decimal('-0.01'), 'deadline': timezone.now().strftime("%Y-%m-%d %H:%M:%S")})
        self.assertContains(response, 'Ensure this value is greater than or equal to 0.')
        
    def test_non_negative_min_price(self):
        """
        A non-negative minimum price is accepted.
        """
        User.objects.create_user('user1', 'user1@example.com', 'very_easy_password')
        self.client.login(username = 'user1', password = 'very_easy_password')
        response = self.client.post(reverse('auction:new_auction'), {'title': 'Auction title', 'item_description': 'Item description', 'price': Decimal('0.00'), 'deadline': timezone.now().strftime("%Y-%m-%d %H:%M:%S")})
        self.assertNotContains(response, 'Ensure this value is greater than or equal to 0.')
        
    def test_wrongly_formatted_deadline(self):
        """
        A wrongly formatted deadline is rejected.
        """
        User.objects.create_user('user1', 'user1@example.com', 'very_easy_password')
        self.client.login(username = 'user1', password = 'very_easy_password')
        time = timezone.localtime(timezone.now())
        response = self.client.post(reverse('auction:new_auction'), {'choice': 'yes', 'title': 'Auction title', 'item_description': 'Item description', 'price': Decimal('0.00'), 'deadline': 'when pigs fly'})
        self.assertContains(response, 'Enter a valid date/time.')

    def test_early_deadline(self):
        """
        A deadline of less than three days from now, is set to three days from now.
        """
        User.objects.create_user('user1', 'user1@example.com', 'very_easy_password')
        self.client.login(username = 'user1', password = 'very_easy_password')
        time = timezone.localtime(timezone.now())
        self.client.post(reverse('auction:new_auction_confirm'), {'choice': 'yes', 'title': 'Auction title', 'item_description': 'Item description', 'price': Decimal('0.00'), 'deadline': time.strftime("%Y-%m-%d %H:%M:%S.%f")})
        auction = Auction.objects.latest('id')
        self.assertTrue(auction.deadline >= time.astimezone(pytz.utc) + timedelta(days = 3) and auction.deadline <= timezone.now() + timedelta(days = 3))
    
    def test_late_deadline(self):
        """
        A deadline of at least three days from now is accepted as is.
        """
        User.objects.create_user('user1', 'user1@example.com', 'very_easy_password')
        self.client.login(username = 'user1', password = 'very_easy_password')
        time = timezone.localtime(timezone.now() + timedelta(hours = 73))
        print(time)
        self.client.post(reverse('auction:new_auction_confirm'), {'choice': 'yes', 'title': 'Auction title', 'item_description': 'Item description', 'price': Decimal('0.00'), 'deadline': time.strftime("%Y-%m-%d %H:%M:%S.%f")}).content
        auction = Auction.objects.latest('id')
        self.assertEqual(auction.deadline, time.astimezone(pytz.utc))
        
        
class BidTests(TestCase):

    def test_no_auction_specified(self):
        """
        Accessing the bid URL without specifying an auction ID results in 404.
        """
        response = self.client.get('/auctions/bid/')
        self.assertEqual(response.status_code, 404)
        
    def test_nonexistent_auction_specified(self):
        """
        Trying to access a nonexistent auction results in 404.
        """
        User.objects.create_user('user1', 'user1@example.com', 'very_easy_password')
        self.client.login(username = 'user1', password = 'very_easy_password')
        response = self.client.get(reverse('auction:bid', kwargs = {'pk': 1}))
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_user(self):
        """
        Unauthenticated users are redirected to login page.
        """
        response = self.client.get(reverse('auction:bid', kwargs = {'pk': 1}))
        self.assertEqual(response.status_code, 302)
        
    def test_bid_wrongly_formatted(self):
        """
        A wrongly formatted bid is rejected.
        """
        User.objects.create_user('user1', 'user1@example.com', 'very_easy_password')
        old_deadline = timezone.now() + timedelta(minutes = 5)
        Auction(seller = 'user1', title = 'Auction title', item_description = 'Item description.', price = Decimal('0.00'), deadline = old_deadline).save()
        id = Auction.objects.latest('id').id
        User.objects.create_user('user2', 'user2@example.com', 'very_easy_password')
        self.client.login(username = 'user2', password = 'very_easy_password')
        response = self.client.post(reverse('auction:bid', kwargs = {'pk': id}), {'price': 'one gazillion euros', 'item_description': 'Item description.'})
        self.assertContains(response, 'Enter a number.')
        
    def test_bid_on_own_auction(self):
        """
        A bid on the user's own auction is rejected.
        """
        User.objects.create_user('user1', 'user1@example.com', 'very_easy_password')
        self.client.login(username = 'user1', password = 'very_easy_password')
        Auction(seller = 'user1', title = 'Auction title', item_description = 'Item description.', price = Decimal('0.00'), deadline = timezone.now() + timedelta(days = 30)).save()
        response = self.client.get(reverse('auction:bid', kwargs = {'pk': Auction.objects.latest('id').id}))
        self.assertEqual(response.status_code, 403)
        
    def test_bid_on_inactive_auction(self):
        """
        A bid on an inactive auction is rejected.
        """
        User.objects.create_user('user1', 'user1@example.com', 'very_easy_password')
        Auction(seller = 'user1', status = Auction.BANNED, title = 'Auction title', item_description = 'Item description.', price = Decimal('0.00'), deadline = timezone.now() + timedelta(days = 30)).save()
        User.objects.create_user('user2', 'user2@example.com', 'very_easy_password')
        self.client.login(username = 'user2', password = 'very_easy_password')
        response = self.client.get(reverse('auction:bid', kwargs = {'pk': Auction.objects.latest('id').id}))
        self.assertEqual(response.status_code, 403)
    
    def test_bid_equals_previous_bid(self):
        """
        A bid that is not higher than the previous bid is rejected.
        """
        User.objects.create_user('user1', 'user1@example.com', 'very_easy_password')
        Auction(seller = 'user1', title = 'Auction title', item_description = 'Item description.', price = Decimal('1.00'), deadline = timezone.now() + timedelta(days = 30)).save()
        User.objects.create_user('user2', 'user2@example.com', 'very_easy_password')
        self.client.login(username = 'user2', password = 'very_easy_password')
        id = Auction.objects.latest('id').id
        self.client.post(reverse('auction:bid', kwargs = {'pk': id}), {'price': Decimal('1.00'), 'item_description': 'Item description.'})
        self.assertEqual(Auction.objects.get(id = id).last_bidder, '')
        
    def test_bid_within_five_minutes_of_deadline(self):
        """
        If a bid is made within five minutes of the deadline, the deadline is extended by five minutes.
        """
        User.objects.create_user('user1', 'user1@example.com', 'very_easy_password')
        old_deadline = timezone.now() + timedelta(minutes = 5)
        Auction(seller = 'user1', title = 'Auction title', item_description = 'Item description.', price = Decimal('0.00'), deadline = old_deadline).save()
        id = Auction.objects.latest('id').id
        User.objects.create_user('user2', 'user2@example.com', 'very_easy_password')
        self.client.login(username = 'user2', password = 'very_easy_password')
        self.client.post(reverse('auction:bid', kwargs = {'pk': id}), {'price': Decimal('0.01'), 'item_description': 'Item description.'})
        self.assertEqual(Auction.objects.get(pk = id).deadline, old_deadline + timedelta(minutes = 5))
        
    def test_bid_earlier_than_five_minutes_from_deadline(self):
        """
        If a bid is made earlier than five minutes from the deadline, the deadline is unchanged.
        """
        User.objects.create_user('user1', 'user1@example.com', 'very_easy_password')
        old_deadline = timezone.now() + timedelta(hours = 1)
        Auction(seller = 'user1', title = 'Auction title', item_description = 'Item description.', price = Decimal('0.00'), deadline = old_deadline).save()
        id = Auction.objects.latest('id').id
        User.objects.create_user('user2', 'user2@example.com', 'very_easy_password')
        self.client.login(username = 'user2', password = 'very_easy_password')
        self.client.post(reverse('auction:bid', kwargs = {'pk': id}), {'price': Decimal('0.01'), 'item_description': 'Item description.'})
        self.assertEqual(Auction.objects.get(pk = id).deadline, old_deadline)
        
        
class ConcurrencyTests(TestCase):

    def test_description_changed_while_bidding(self):
        """
        A bid is rejected if the auction description changed while the bid was being made.
        """
        User.objects.create_user('user1', 'user1@example.com', 'very_easy_password')
        Auction(seller = 'user1', title = 'Auction title', item_description = 'Item description.', price = Decimal('0.00'), deadline = timezone.now() + timedelta(days = 30)).save()
        auction = Auction.objects.latest('id')
        User.objects.create_user('user2', 'user2@example.com', 'very_easy_password')
        self.client.login(username = 'user2', password = 'very_easy_password')
        response = self.client.get(reverse('auction:bid', kwargs = {'pk': auction.id}))
        old_item_description = response.context['form'].instance.item_description
        auction.item_description = 'Edited item description.'
        auction.save()
        self.client.post(reverse('auction:bid', kwargs = {'pk': auction.id}), {'item_description': old_item_description, 'price': Decimal('0.01')})
        self.assertEqual(Auction.objects.get(pk = auction.id).last_bidder, '')
        
    def test_outbid_while_bidding(self):
        """
        A bid is rejected if someone outbid it while it was being made.
        """
        User.objects.create_user('user1', 'user1@example.com', 'very_easy_password')
        Auction(seller = 'user1', title = 'Auction title', item_description = 'Item description.', price = Decimal('0.00'), deadline = timezone.now() + timedelta(days = 30)).save()
        auction = Auction.objects.latest('id')
        User.objects.create_user('user2', 'user2@example.com', 'very_easy_password')
        self.client.login(username = 'user2', password = 'very_easy_password')
        response = self.client.get(reverse('auction:bid', kwargs = {'pk': auction.id}))
        old_price = response.context['form'].instance.price
        auction.price = old_price + Decimal('0.01')
        auction.save()
        self.client.post(reverse('auction:bid', kwargs = {'pk': auction.id}), {'item_description': auction.item_description, 'price': old_price + Decimal('0.01')})
        self.assertEqual(Auction.objects.get(pk = auction.id).last_bidder, '')