from django.contrib import admin
from .models import InvestmentPlan, UserInvestment, UserBalance

admin.site.register(InvestmentPlan)
admin.site.register(UserInvestment)
admin.site.register(UserBalance)
