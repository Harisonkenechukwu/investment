from django.contrib import admin
from .models import Profile
from investment.models import UserReferral

admin.site.register(Profile)

@admin.register(UserReferral)
class UserReferralAdmin(admin.ModelAdmin):
    list_display = ('user', 'referral_code', 'referred_by', 'referral_count', 'referral_earnings')
    search_fields = ('user__username', 'referral_code', 'referred_by__username')
