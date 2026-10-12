import re


def support_agent(message: str) -> str:
    """A deterministic, key-free customer support agent for repeatable demos."""
    text = message.casefold()
    if any(word in text for word in ("refund", "return", "money back")):
        return "I can help with a refund. Please share your order number; eligible purchases can be returned within 30 days."
    if any(word in text for word in ("shipping", "delivery", "tracking", "where is my order")):
        order = re.search(r"(?:order\s*#?\s*|#)([A-Z0-9-]{4,})", message, re.I)
        reference = f" for order {order.group(1)}" if order else ""
        return f"I can help track your shipment{reference}. Standard delivery takes 3–5 business days; share your order number for a tracking update."
    if any(word in text for word in ("password", "login", "sign in", "account")):
        return "To reset your password, select Forgot password on the sign-in page. We will email you a secure reset link."
    if any(word in text for word in ("cancel", "stop order")):
        return "I can help cancel an order before it ships. Please provide your order number so I can check its status."
    if any(word in text for word in ("price", "cost", "plan")):
        return "You can find current pricing on our plans page. I can help compare options if you share what you need."
    return "Thanks for reaching out. I am here to help with orders, shipping, returns, account access, or product questions."
