from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    JobListingViewSet, 
    EmailSubscriberViewSet, 
    ScrapingLogViewSet,
    home,
    job_list,
    job_detail,
    subscribe,
    trigger_scrape
)

router = DefaultRouter()
router.register(r'jobs', JobListingViewSet, basename='job')
router.register(r'subscribers', EmailSubscriberViewSet, basename='subscriber')
router.register(r'logs', ScrapingLogViewSet, basename='log')

urlpatterns = [
    # Web Interface
    path('', home, name='home'),
    path('jobs/', job_list, name='job_list'),
    path('jobs/<int:job_id>/', job_detail, name='job_detail'),
    path('subscribe/', subscribe, name='subscribe'),
    path('trigger-scrape/', trigger_scrape, name='trigger_scrape'),
    
    # API Endpoints
    path('api/', include(router.urls)),
]