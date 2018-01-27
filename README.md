Implemented requirements
Part 1
    • UC3: create auction
    • UC4: edit auction description
    • UC5: browse & search
    • UC11: currency exchange
Part 2
    • UC1: create user
    • UC2: edit user
    • UC6: bid
    • UC7: ban auction
    • WS1: Browse & Search API
    • WS2: bid API
    • UC8: Resolve auction
    • OP2: Soft deadlines for bidding
        ◦ “If a user bids at an auction within five minutes of the auction deadline, the auction deadline is extended automatically for an additional five minutes. This allows other users to place new bids”. The phrase “additional five minutes” was interpreted to mean adding five minutes to the deadline, as opposed to setting the deadline to five minutes from now. The following code was used:
if auction.deadline - timezone.now() < timedelta(minutes = 5):
    auction.deadline += timedelta(minutes = 5)
Part 3
    • UC9: language switching
    • OP3: store language preference
        ◦ Implemented by creating model AuctionUser, which has a one-to-one relationship with django’s built-in User model. AuctionUser has a field that contains the user’s language preference.
    • OP1: send seller auction link
        ◦ Code:
send_mail('Auction created', 'Your auction was successfully created. 		Link to auction details:
		https://pengstro.pythonanywhere.com/auction/'
		+ str(auction.pk), 'pengstro@abo.fi', [request.user.email])
    • UC10: concurrency
    • TR1: Database fixture and data generation program
    • TR2.1: Functional tests for UC3
    • TR2.2: Functional tests for UC6
    • TR2.3: Functional tests for UC10
Requirements
Django==1.11.1
pytz==2017.2
Admin credentials
Username: admin
Password: very_easy_password
Session management
Users are logged in and out using the built-in django.contrib.auth.views.LoginView and .LogoutView, respectively. The @login_required decorator is used to limit access to whole pages, while the is_authenticated() function of the built-in django.contrib.auth.models.User class is used to show specific parts of a page only to logged-in users.
UC3 confirmation form
The confirmation form has five hidden input fields containing the auction data, which is passed through a POST request from the preceding form, where the auction data is entered by the user. In addition, the confirmation form has two radio buttons with the options “Yes” and “No”; the user’s choice is submitted when he or she presses the “Submit” button.
UC8 automatic bid resolution
This is implemented using a custom Django management command, named “resolve”, which is called at regular intervals by the following Linux command:
while sleep 60; do python /home/pengstro/web-services-2017-project-part2-pengstro/source/manage.py resolve; done &
Concurrency in UC6
This is handled using a combination of a “locked_by” field in the auction, and checking that neither the item description nor highest bid has changed while bidding. For example:
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
WS1: Browse & Search API
The browsing API is used by sending a GET request to pengstro.pythonanywhere.com/auctions/ , for instance:
curl pengstro.pythonanywhere.com/auctions/
Please note the slash at the end of the URL is required.
The service might respond with:
{"data": {"id": "1", "title": "auction1", "seller": "user1", "item_description": "item1", "highest_bid": "1.07", "deadline": "2017-10-16T10:09:14.668Z"}}
A specific auction can also be requested:
curl pengstro.pythonanywhere.com/auctions/1/
The search API is used by a GET request with the parameter “title” to pengstro.pythonanywhere.com/auctions/ , for instance:
curl pengstro.pythonanywhere.com/auctions/?title=auction1
The slash between “auctions” and “?title” is required.
WS2: bid API
The bidding API is used by sending a POST request to pengstro.pythonanywhere.com/bids/ . The request header must contain the user’s credentials (username and password) and the request body must contain the bid (auction ID and bid amount) in JSON format. For instance:
curl -u user2:password2 --data '{"auction_id": "1", "bid": "1.08"}' pengstro.pythonanywhere.com/bids/
Again, the trailing slash is required.
The service might respond with:
HTTP 1.1 201 Created
Content-Type: application/json
Location: http://pengstro.pythonanywhere.com/bids/4/
{"data": {"id": "4", "auction_id": "1", "bidder": "user2", "amount": "1.08"}}
Or, if there was an error, for example incorrect username or password:
HTTP 1.1 401 Unauthorized
Content-Type: application/json
{"detail": "Incorrect username or password"}
The user can also get the data on a specific bid by GET request:
curl -u user2:password2 pengstro.pythonanywhere.com/bids/4/
Functional tests
    • Tested the creation of an auction, using the following parameters:
        ◦ (Un)authenticated user - Unauthenticated users are redirected to login page.
        ◦ (In)correctly formatted minimum price - A wrongly formatted price is rejected.
        ◦ (Non-)negative minimum price - A negative minimum price is rejected.
        ◦ (In)correctly formatted deadline - A wrongly formatted deadline is rejected.
        ◦ Early/late deadline - A deadline of less than three days from now, is set to three days from now.
    • Tested bidding on an auction, using the following parameters:
        ◦ No auction specified - Accessing the bid URL without specifying an auction ID results in 404.
        ◦ (Non)existent auction specified - Trying to access a nonexistent auction results in 404.
        ◦ (Un)authenticated user - Unauthenticated users are redirected to login page.
        ◦ (In)correctly formatted bid - A wrongly formatted bid is rejected.
        ◦ Bidding on own/someone else’s auction - A bid on the user's own auction is rejected.
        ◦ Bidding on (in)active auction - A bid on an inactive auction is rejected.
        ◦ Making a bid that is no higher than the currently highest bid - A bid that is not higher than the previous bid is rejected.
        ◦ Bidding within five minutes of deadline/earlier than five minutes from deadline - If a bid is made within five minutes of the deadline, the deadline is extended by five minutes.
    • Tested concurrency, using the following parameters:
        ◦ Description (un)changed while bidding - A bid is rejected if the auction description changed while the bid was being made.
        ◦ (Not) outbid while bidding - A bid is rejected if someone outbid it while it was being made.
UC9 Language switching
Implemented using i18n, “trans” tags, and django.utils.translation. The following code is used in the View that handles language switching:
language = form.cleaned_data['language']
translation.activate(language)
self.request.session[translation.LANGUAGE_SESSION_KEY] = language
Data generation program
    • Data was generated using a custom command, “populatedatabase”, located in [source/]auction/management/commands/populatedatabase.py . The command is used as an argument to manage.py: python manage.py populatedatabase
    • The fixture is located in [source/]auction/fixtures/db_data.json.