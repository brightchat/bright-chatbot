from models.subscription_plan import SubscriptionPlan

# Brightbot Subscription plans:
BasicPlan = SubscriptionPlan(
    id="basic",
    name="BrightBot Basic",
    description="Basic Free plan for BrightBot",
    sessions_quota=None,
    messages_quota=20,
    image_generation_quota=1,
    image_resolution_size="small",
)

StandardPlan = SubscriptionPlan(
    id="standard",
    name="BrightBot Standard",
    description="Standard plan for BrightBot, sold at $4.99/month",
    sessions_quota=None,
    messages_quota=100,
    image_generation_quota=5,
    image_resolution_size="medium",
    quota_reset_period="day",
)

PremiumPlan = SubscriptionPlan(
    id="premium",
    name="BrightBot Premium",
    description="Premium plan for BrightBot, sold at $14.99/month",
    sessions_quota=None,
    messages_quota=500,
    image_generation_quota=20,
    image_resolution_size="large",
    quota_reset_period="day",
)
