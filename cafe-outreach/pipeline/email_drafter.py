FLAVOR_MAP = {
    "acai":      ["Mix Berry", "Coconut Cranberry", "Mango Coconut"],
    "berry":     ["Mix Berry", "Coconut Cranberry", "Lemon Honey"],
    "tropical":  ["Mango Coconut", "Pina Colada", "Coconut Cranberry"],
    "chocolate": ["Coffee Chocolate", "Chocolate Salted Caramel", "Almond Dark Chocolate"],
    "coffee":    ["Coffee Chocolate", "Coffee", "Masala Chai"],
    "matcha":    ["Lemon Honey", "Mix Seeds & Fruit", "Coconut Cranberry"],
    "default":   ["Mix Berry", "Mango Coconut", "Masala Chai", "Coffee Chocolate"],
}


def pick_flavors(menu_hint: str = "") -> list:
    hint = menu_hint.lower()
    if "acai" in hint:
        return FLAVOR_MAP["acai"]
    if "berry" in hint or "blueberry" in hint or "strawberry" in hint:
        return FLAVOR_MAP["berry"]
    if "tropical" in hint or "pineapple" in hint or "mango" in hint:
        return FLAVOR_MAP["tropical"]
    if "chocolate" in hint or "mocha" in hint:
        return FLAVOR_MAP["chocolate"]
    if "coffee" in hint or "espresso" in hint:
        return FLAVOR_MAP["coffee"]
    if "matcha" in hint:
        return FLAVOR_MAP["matcha"]
    return FLAVOR_MAP["default"]


def generate_email(cafe_name: str, contact_name: str = "", menu_hint: str = "") -> tuple:
    greeting = f"Hi {contact_name}" if contact_name else "Hi there"
    flavors = pick_flavors(menu_hint)
    flavor_lines = "\n".join(f"- {f}" for f in flavors)

    subject = "Granola toppings your bowls will love - The Recipe Tailor"
    body = f"""{greeting},

I came across {cafe_name} and love what you are doing with your menu - it is exactly the kind of place we love partnering with.

I am from The Recipe Tailor, a Bangalore-based brand making small-batch, guilt-free granolas and cookies in flavours you will not find anywhere else.

A few that tend to work really well as bowl toppings:
{flavor_lines}

All made with clean ingredients, your choice of sweetener (desi khand, coconut sugar, or regular), and an optional protein boost. We supply in bulk from Rs. 430/kg.

Happy to send you a sample pack so your team can try before committing to anything.

Would a quick call or visit work this week?

Warm regards,
Naman
The Recipe Tailor
[Phone Number]
[Instagram Handle]"""

    return subject, body


def generate_instagram_dm(cafe_name: str, menu_hint: str = "") -> str:
    flavors = pick_flavors(menu_hint)
    top_flavors = ", ".join(flavors[:2])

    return f"""Hi! Love what you are doing at {cafe_name}.

I am Naman from The Recipe Tailor - we make small-batch, guilt-free granolas in interesting flavours ({top_flavors} and more). Would love to partner with you as a topping option for your bowls.

We supply B2B from Rs. 430/kg and are happy to send a sample pack first. Would that work?"""
