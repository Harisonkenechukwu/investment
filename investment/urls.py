from django.urls import path
from . import views

app_name = 'investment'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('recovery/', views.recovery, name='recovery'),
    path('plans/', views.investment_plans, name='investment_plans'),
    path('choose/<int:plan_id>/', views.choose_plan, name='choose_plan'),
    path('payment/<int:plan_id>/', views.payment_page, name='payment'),
    path('', views.landing_page, name='landing_page'),  # Landing page URL
    path('testimonials/', views.testimonials_page, name='testimonials_page'),  # Testimonials page URL
    path('about/', views.about, name='about'),
    path('news/', views.news_feed, name='news_feed'),
    path('education/', views.educational_resources, name='educational_resources'),
    path('deposit/', views.initiate_deposit, name='initiate_deposit'),
    path('deposit/success/', views.payment_success, name='payment_success'),
    path('deposit/cancel/', views.payment_cancel, name='payment_cancel'),
    path('deposit/cryptomus/callback/', views.cryptomus_callback, name='cryptomus_callback'),  # Updated this line
    path('referral-program/', views.referral_program, name='referral_program'),
]
