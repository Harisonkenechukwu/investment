from pyexpat.errors import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import InvestmentPlan, UserInvestment, UserBalance
from datetime import timedelta, date
from django.urls import reverse
from django.contrib.auth import logout
from django.utils import timezone
from decimal import Decimal
import os
import requests
from django.shortcuts import render
from django.http import JsonResponse
from django.core.cache import cache
from django.shortcuts import render
from datetime import date
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from decimal import Decimal
from .models import UserInvestment, UserBalance  # Ensure your models are imported
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from decimal import Decimal
from datetime import date
from .models import UserBalance, UserInvestment, UserReferral
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Deposit
from .forms import DepositForm
from .utils.stripe_utils import create_stripe_payment_session
from .utils.cryptomus_utils import create_cryptomus_invoice
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Deposit
import stripe
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Deposit
from django.shortcuts import render, redirect
from django.urls import reverse
from .models import Deposit
from .utils.stripe_utils import create_stripe_payment_session
from .utils.cryptomus_utils import create_cryptomus_invoice
### views.py
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Deposit
from .utils.stripe_utils import create_stripe_payment_session
from .utils.cryptomus_utils import create_cryptomus_invoice, verify_signature


@login_required
def referral_program(request):
    user = request.user
    context = {
        'referral_code': user.referral.referral_code,
        'referral_count': user.referral.referral_count,
        'referral_earnings': user.referral.referral_earnings,
    }
    return render(request, 'referral_program.html', context)


@login_required
def initiate_deposit(request):
    if request.method == "POST":
        amount = request.POST.get('amount')
        payment_gateway = request.POST.get('payment_gateway')

        if not amount or not payment_gateway:
            return render(request, 'initiate_deposit.html', {'error': 'Amount and payment gateway are required.'})

        try:
            amount = float(amount)
            deposit = Deposit.objects.create(user=request.user, amount=amount, payment_gateway=payment_gateway)
        except Exception as e:
            print(f"Error initiating deposit: {e}")
            return render(request, 'initiate_deposit.html', {'error': 'Deposit initiation failed.'})

        if payment_gateway == 'stripe':
            session_url = create_stripe_payment_session(deposit)
            if session_url:
                return redirect(session_url)

        elif payment_gateway == 'cryptomus':
            callback_url = request.build_absolute_uri(reverse('investment:cryptomus_callback'))  # Updated this line
            success_url = request.build_absolute_uri(reverse('investment:payment_success'))  # Updated this line
            invoice = create_cryptomus_invoice(amount, request.user.id, callback_url, success_url)
            if invoice and 'url' in invoice['result']:
                deposit.transaction_id = invoice['result']['order_id']
                deposit.save()
                return redirect(invoice['result']['url'])

        return render(request, 'initiate_deposit.html', {'error': 'Payment setup failed.'})

    return render(request, 'initiate_deposit.html')



def payment_success(request):
    return render(request, 'payment_success.html')

def payment_cancel(request):
    return render(request, 'payment_cancel.html')

@csrf_exempt
def cryptomus_callback(request):
    if request.method == 'POST':
        data = request.POST

        # Verify the payment signature (if provided)
        signature = request.META.get('HTTP_SIGNATURE')
        if signature and not verify_signature(API_KEY, data, signature):
            return JsonResponse({'status': 'error', 'message': 'Invalid signature'}, status=400)

        order_id = data.get('order_id')
        status = data.get('status')

        try:
            deposit = Deposit.objects.get(transaction_id=order_id)
            if status == 'paid':
                deposit.is_successful = True
                deposit.save()
            return JsonResponse({'status': 'success'}, status=200)
        except Deposit.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Invalid transaction ID'}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)




@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    endpoint_secret = "your_stripe_webhook_secret"

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        return JsonResponse({'status': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError as e:
        return JsonResponse({'status': 'Invalid signature'}, status=400)

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        deposit_id = session['metadata']['deposit_id']
        try:
            deposit = Deposit.objects.get(id=deposit_id)
            deposit.is_successful = True
            deposit.save()
        except Deposit.DoesNotExist:
            return JsonResponse({'status': 'Deposit not found'}, status=400)

    return JsonResponse({'status': 'success'}, status=200)



@login_required
def deposit(request):
    if request.method == 'POST':
        form = DepositForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            gateway = form.cleaned_data['payment_gateway']

            deposit = Deposit.objects.create(
                user=request.user,
                amount=amount,
                is_successful=False,
                payment_gateway=gateway,
            )

            if gateway == 'stripe':
                session_url = create_stripe_payment_session(deposit)
                if session_url:
                    return redirect(session_url)
            elif gateway == 'cryptomus':
                callback_url = request.build_absolute_uri(reverse('cryptomus_callback'))
                success_url = request.build_absolute_uri(reverse('payment_success'))
                invoice = create_cryptomus_invoice(amount, request.user.id, callback_url, success_url)
                if invoice and 'url' in invoice['result']:
                    deposit.transaction_id = invoice['result']['order_id']
                    deposit.save()
                    return redirect(invoice['result']['url'])

            messages.error(request, 'Payment setup failed.')
            return render(request, 'deposit/error.html')
    else:
        form = DepositForm()

    return render(request, 'deposit/deposit_form.html', {'form': form})


@login_required
def dashboard(request):
    # Fetch or create the user's balance
    user_balance, created = UserBalance.objects.get_or_create(user=request.user, defaults={'balance': 0})

    # Get all active investments for the user
    active_investments = UserInvestment.objects.filter(user=request.user, is_active=True)
    
    total_investment = sum(investment.plan.trading_amount for investment in active_investments)
    total_earnings = Decimal('0.00')
    
    current_date = timezone.now().date()

    for investment in active_investments:
        # Update earnings if the last update was before today
        if investment.last_earning_update < current_date:
            days_to_update = (current_date - investment.last_earning_update).days
            days_active = min(days_to_update, 30)  # Limit to 30 days
            
            daily_earnings = investment.plan.daily_profit * days_active
            investment.total_earnings += daily_earnings
            investment.last_earning_update = current_date
            investment.save()

        total_earnings += investment.total_earnings

        # Add progress bar calculation
        total_days = (investment.end_date - investment.start_date).days
        elapsed_days = (date.today() - investment.start_date).days
        progress = int((elapsed_days / total_days) * 100) if total_days > 0 else 0

        # Attach progress data to each investment object
        investment.progress_percentage = min(max(progress, 0), 100)
        investment.elapsed_days = max(elapsed_days, 0)
        investment.total_days = total_days

    # Calculate wallet balance and net worth
    wallet_balance = user_balance.balance + total_earnings
    net_worth = wallet_balance + total_investment

        # Fetch or create user's referral information
    # Fetch or create user's referral information
    user_referral, created = UserReferral.objects.get_or_create(
        user=request.user
    )

    if created:
        user_referral.referral_code = user_referral.generate_referral_code()
        user_referral.save()

    # Pass data to the template
    context = {
        'wallet_balance': wallet_balance,
        'net_worth': net_worth,
        'total_earnings': total_earnings,
        'investments': active_investments,
        'capital': user_balance.balance,
        # Add referral information to context
        'referral_code': user_referral.referral_code,
        'referral_count': user_referral.referral_count,
        'referral_earnings': user_referral.referral_earnings,
    }

    return render(request, 'dashboard.html', context)





def educational_resources(request):
    resources = [
        {
            'title': 'Introduction to Investing',
            'description': 'Learn the basics of investing and how to get started.',
            'type': 'article',
            'url': '#',
        },
        {
            'title': 'Understanding Stock Markets',
            'description': 'A comprehensive guide to how stock markets work.',
            'type': 'video',
            'url': '#',
        },
        {
            'title': 'Diversification Strategies',
            'description': 'Learn how to spread your investments to manage risk.',
            'type': 'tutorial',
            'url': '#',
        },
        {
            'title': 'Fundamental Analysis',
            'description': 'How to analyze companies for investment potential.',
            'type': 'article',
            'url': '#',
        },
        {
            'title': 'Technical Analysis Basics',
            'description': 'Introduction to reading and understanding stock charts.',
            'type': 'video',
            'url': '#',
        },
        {
            'title': 'Retirement Planning 101',
            'description': 'Essential strategies for planning your retirement investments.',
            'type': 'tutorial',
            'url': '#',
        },
    ]
    return render(request, 'investment/educational_resources.html', {'resources': resources})



def news_feed(request):
    # Check if news data is in cache
    cached_news = cache.get('news_data')
    if cached_news:
        return render(request, 'investment/news_feed.html', {'news_items': cached_news})

    # If not in cache, fetch from API
    api_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
    url = f'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&apikey={api_key}'
    
    try:
        response = requests.get(url)
        data = response.json()
        news_items = data.get('feed', [])[:10]  # Get the first 10 news items
        
        # Cache the news data for 1 hour (3600 seconds)
        cache.set('news_data', news_items, 3600)
        
        return render(request, 'investment/news_feed.html', {'news_items': news_items})
    except Exception as e:
        return render(request, 'investment/news_feed.html', {'error': str(e)})




    
# Investment Plans Page
@login_required
def investment_plans(request):
    plans = InvestmentPlan.objects.all()
    return render(request, 'investment/plans.html', {'plans': plans})

# Choose Investment Plan
@login_required
def choose_plan(request, plan_id):
    # Check if the user already has an active investment
    if UserInvestment.objects.filter(user=request.user, is_active=True).exists():
        # Redirect to the dashboard or show an error message
        return redirect('dashboard.')  # You can replace this with a message or alert if you prefer

    plan = get_object_or_404(InvestmentPlan, id=plan_id)
    
    if request.method == 'POST':
        user_balance = UserBalance.objects.get(user=request.user)
        
        # Ensure the user has enough balance to proceed with the investment
        if user_balance.balance >= plan.trading_amount:
            user_balance.balance -= plan.trading_amount
            user_balance.save()

            # Set the investment's end date (30 days from today)
            end_date = date.today() + timedelta(weeks=4)  # 1-month program
            
            # Create a new investment for the user
            UserInvestment.objects.create(user=request.user, plan=plan, end_date=end_date)
            
            # Redirect to the payment page
            return redirect('investment:payment', plan_id=plan_id)
        else:
            # Handle insufficient balance
            return render(request, 'investment/insufficient_balance.html')

    return render(request, 'investment/choose_plan.html', {'plan': plan})

# Payment Page
@login_required
def payment_page(request, plan_id):
    plan = get_object_or_404(InvestmentPlan, id=plan_id)
    return render(request, 'investment/payment.html', {'plan': plan})





# Landing Page View
def landing_page(request):
    return render(request, 'landing.html')

# Testimonials Page View
def testimonials_page(request):
    return render(request, 'testimony.html')

def about(request):
    return render(request, 'about/about.html')


def logout_view(request):
    logout(request)
    return redirect(reverse('login'))

def recovery(request):
    return render(request, 'recovery.html')



