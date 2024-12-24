from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
class Deposit(models.Model):
    GATEWAY_CHOICES = [
        ('stripe', 'Stripe'),
        ('cryptomus', 'Cryptomus'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    deposit_date = models.DateTimeField(auto_now_add=True)
    is_successful = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_gateway = models.CharField(max_length=20, choices=GATEWAY_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.amount} USD ({self.payment_gateway})"


class UserReferral(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='referral')
    referral_code = models.CharField(max_length=12, unique=True, default=uuid.uuid4().hex[:12].upper())
    referred_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='referrals')
    referral_earnings = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    referral_count = models.PositiveIntegerField(default=0)

    
    def generate_referral_code(self):
        if not self.referral_code:
            self.referral_code = str(uuid.uuid4())[:8]
        return self.referral_code

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        super().save(*args, **kwargs)

    def update_total_referrals(self):
        self.total_referrals = User.objects.filter(userreferral__referred_by=self.user).count()
        self.save()

@receiver(post_save, sender=User)
def create_user_referral(sender, instance, created, **kwargs):
    if created:
        UserReferral.objects.create(user=instance)

@receiver(post_save, sender=UserReferral)
def update_referrer_total(sender, instance, created, **kwargs):
    if instance.referred_by:
        referrer_profile = UserReferral.objects.get(user=instance.referred_by)
        referrer_profile.update_total_referrals()


 
class InvestmentPlan(models.Model):
    name = models.CharField(max_length=50)
    trading_amount = models.DecimalField(max_digits=10, decimal_places=2)
    daily_profit = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

class UserInvestment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="investments")
    plan = models.ForeignKey(InvestmentPlan, on_delete=models.CASCADE)
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    last_earning_update = models.DateField(default=timezone.now)
    total_earnings = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"

class UserBalance(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="balance")
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user.username} - {self.balance}"

