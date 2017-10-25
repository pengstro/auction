from django.conf.urls import include, url
from django.contrib import admin

from auction import views

urlpatterns = [
    url(r'^$', views.AuctionListView.as_view(), name='index'),
    url(r'^(?P<pk>[0-9]+)/$', views.AuctionDetailView.as_view(), name='detail'),
    url(r'^auctions/', include('auction.urls')),
    url(r'^bids/$', views.BidAPIView.as_view(), name = 'bid_api'),
    url(r'^bids/(?P<pk>[0-9]+)/$', views.BidDetailAPIView.as_view(), name = 'bid_detail_api'),
    url(r'^admin/', admin.site.urls),
]