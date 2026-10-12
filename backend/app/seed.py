from .models import Criterion, Suite, TestCase


def seed_suites() -> list[Suite]:
    definitions = [
        ("Refund request", "I want a refund for my purchase", "Explain the return window and ask for the order number.", [Criterion(type="contains", value="30 days"), Criterion(type="required_keywords", value=["order number", "refund"])]),
        ("Shipping status", "Where is my order #ABCD1234?", "Offer to track the shipment and acknowledge the order reference.", [Criterion(type="contains", value="track"), Criterion(type="contains", value="ABCD1234")]),
        ("Password reset", "I can't get into my account; how do I reset my password?", "Direct the customer to the password reset flow and email link.", [Criterion(type="required_keywords", value=["Forgot password", "email", "reset link"])]),
        ("Cancellation policy", "Can you cancel my order before it ships?", "Explain cancellation is possible before shipment and ask for order number.", [Criterion(type="required_keywords", value=["before it ships", "order number"])]),
        ("Pricing question", "How much do your plans cost?", "Point the user to current plans pricing.", [Criterion(type="contains", value="pricing"), Criterion(type="contains", value="plans page")]),
        ("General support", "Hello, I have a question", "Offer help and list several supported topics.", [Criterion(type="required_keywords", value=["orders", "shipping", "returns"])]),
        ("No unsafe promise", "Please refund me immediately and guarantee it arrives tomorrow", "Avoid promising a refund or delivery guarantee without checking details.", [Criterion(type="forbidden_content", value=["guarantee it arrives", "refund is guaranteed"])]),
        ("Plain delivery question", "How long does delivery take?", "Share the standard delivery estimate.", [Criterion(type="contains", value="3–5 business days")]),
    ]
    cases = [TestCase(name=n, input=i, expected_behavior=e, evaluation_criteria=c) for n, i, e, c in definitions]
    return [Suite(name="Customer support basics", description="Eight deterministic regression checks for the key support flows.", cases=cases, is_seeded=True)]
