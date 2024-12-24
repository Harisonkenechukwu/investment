from django import forms
from django.core.validators import MinValueValidator
from django.conf import settings

class DepositForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Enter amount',
            'step': '0.01',
            'min': '1.00',  # Assuming minimum deposit is $1
        }),
        validators=[MinValueValidator(1.00)],
        help_text="Minimum deposit: $1.00"
    )
    payment_gateway = forms.ChoiceField(
        choices=[
            ('stripe', 'Stripe'),
            ('cryptomus', 'Cryptomus'),
        ],
        widget=forms.RadioSelect,
        initial='stripe'  # Set Stripe as the default option
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['amount'].label = "Deposit Amount ($)"
        self.fields['payment_gateway'].label = "Select Payment Method"

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        max_deposit = getattr(settings, 'MAX_DEPOSIT_AMOUNT', 10000)
        if amount > max_deposit:
            raise forms.ValidationError(f"Maximum deposit amount is ${max_deposit}")
        return amount

