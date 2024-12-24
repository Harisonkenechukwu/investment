from django.urls import path
from .views import home, profile, RegisterView
from investment.views import landing_page

urlpatterns = [
    path('', landing_page, name='users-home'),
    path('register/', RegisterView.as_view(), name='users-register'),
    path('profile/', profile, name='users-profile'),
]
