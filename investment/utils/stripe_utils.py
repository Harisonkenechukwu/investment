### utils/stripe_utils.py
import stripe

stripe.api_key = "sk_test_51QDaeyLGShIc565sJkaQBRnSCyKWc3zbILlrdVB5xlyfIkuKbH325KbYKWkNd4MFi601DHlpimnB3QoyBPpXJF9r00AB8F4Iuc"

def create_stripe_payment_session(deposit):
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f"Deposit by {deposit.user.username}",
                    },
                    'unit_amount': int(deposit.amount * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url="https://yourdomain.com/deposit/success/",
            cancel_url="https://yourdomain.com/deposit/cancel/",
            metadata={'deposit_id': deposit.id},
        )
        return session.url
    except Exception as e:
        print(f"Stripe Error: {e}")
        return None