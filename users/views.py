from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordChangeView
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.views import View
from django.contrib.auth.decorators import login_required
from investment.models import UserReferral, UserInvestment, UserBalance
from decimal import Decimal
from .forms import RegisterForm, LoginForm, UpdateUserForm, UpdateProfileForm


def home(request):
    return render(request, 'users/home.html')


class RegisterView(View):
    form_class = RegisterForm
    initial = {'key': 'value'}
    template_name = 'users/register.html'

    def dispatch(self, request, *args, **kwargs):
        # Redirect to the home page if a user tries to access the register page while logged in
        if request.user.is_authenticated:
            return redirect(to='/')

        return super(RegisterView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        # Check for a referral code in the query parameters
        referral_code = request.GET.get('ref', None)
        form = self.form_class(initial=self.initial)
        return render(request, self.template_name, {'form': form, 'referral_code': referral_code})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            # Save the new user
            user = form.save()

            # Handle referral code
            referral_code = request.POST.get('referral_code', None)
            referrer = None
            if referral_code:
                try:
                    referrer = UserReferral.objects.get(referral_code=referral_code).user
                except UserReferral.DoesNotExist:
                    messages.error(request, "Invalid referral code.")

            # Create a referral record for the new user
            UserReferral.objects.create(user=user, referred_by=referrer)

            # Reward the referrer
            if referrer:
                referrer.referral.referral_earnings += Decimal("5.00")  # e.g., $5 reward
                referrer.referral.save()

            # Reward the new user with an initial balance
            UserBalance.objects.create(user=user, balance=Decimal("10.00"))  # e.g., $10 bonus

            # Success message and redirect to login
            messages.success(request, f'Account created for {user.username}')
            return redirect(to='login')

        return render(request, self.template_name, {'form': form})

        


# Class based view that extends from the built in login view to add a remember me functionality
class CustomLoginView(LoginView):
    form_class = LoginForm

    def form_valid(self, form):
        remember_me = form.cleaned_data.get('remember_me')

        if not remember_me:
            # set session expiry to 0 seconds. So it will automatically close the session after the browser is closed.
            self.request.session.set_expiry(0)

            # Set session as modified to force data updates/cookie to be saved.
            self.request.session.modified = True

        # else browser session will be as long as the session cookie time "SESSION_COOKIE_AGE" defined in settings.py
        return super(CustomLoginView, self).form_valid(form)


class ResetPasswordView(SuccessMessageMixin, PasswordResetView):
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    subject_template_name = 'users/password_reset_subject'
    success_message = "We've emailed you instructions for setting your password, " \
                      "if an account exists with the email you entered. You should receive them shortly." \
                      " If you don't receive an email, " \
                      "please make sure you've entered the address you registered with, and check your spam folder."
    success_url = reverse_lazy('users-home')


class ChangePasswordView(SuccessMessageMixin, PasswordChangeView):
    template_name = 'users/change_password.html'
    success_message = "Successfully Changed Your Password"
    success_url = reverse_lazy('users-home')


@login_required
def profile(request):
    if request.method == 'POST':
        user_form = UpdateUserForm(request.POST, instance=request.user)
        profile_form = UpdateProfileForm(request.POST, request.FILES, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile is updated successfully')
            return redirect(to='users-profile')
    else:
        user_form = UpdateUserForm(instance=request.user)
        profile_form = UpdateProfileForm(instance=request.user.profile)

    return render(request, 'users/profile.html', {'user_form': user_form, 'profile_form': profile_form})
