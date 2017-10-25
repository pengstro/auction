from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

from . import views


app_name = 'auction'

# List of valid URL patterns for the auction app.

urlpatterns = [
    url(r'^new_auction/$', views.NewAuctionView.as_view(), name='new_auction'),
    url(r'^new_auction_confirm/$', views.NewAuctionConfirmView.as_view(), name='new_auction_confirm'),
    url(r'^login/$', views.LoginView.as_view(), name='login'),
    url(r'^logout/$', auth_views.LogoutView.as_view(), name = 'logout'),
    url(r'^register/$', views.RegisterView.as_view(), name = 'register'),
    url(r'^register_done/$', views.RegisterDoneView.as_view(), name = 'register_done'),
    url(r'^edit_user/$', views.EditUserView.as_view(), name = 'edit_user'),
    url(r'^edit_email/$', views.EditEmailView.as_view(), name = 'edit_email'),
    url(r'^edit_email_done/$', views.EditEmailDoneView.as_view(), name = 'edit_email_done'),
    url(r'^password_change/$', auth_views.PasswordChangeView.as_view(success_url = reverse_lazy('auction:password_change_done')), name = 'password_change'),
    url(r'^password_change_done/$', auth_views.PasswordChangeDoneView.as_view(), name = 'password_change_done'),
    url(r'^edit_description/(?P<pk>[0-9]+)/$', views.EditDescriptionView.as_view(), name = 'edit_description'),
    url(r'^search/$', views.SearchView.as_view(), name = 'search'),
    url(r'^bid/(?P<pk>[0-9]+)/$', views.BidView.as_view(), name = 'bid'),
    url(r'^ban/(?P<pk>[0-9]+)/$', views.BanView.as_view(), name = 'ban'),
    url(r'^$', views.AuctionListAPIView.as_view(), name = 'auction_list_api'),
    url(r'^(?P<pk>[0-9]+)/$', views.AuctionDetailAPIView.as_view(), name = 'auction_detail_api'),
    url(r'^change_language/$', views.ChangeLanguageView.as_view(), name = 'change_language'),
]