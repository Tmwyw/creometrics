"""Debug script to check environment variables."""
import os

print("\n=== ENVIRONMENT VARIABLES DEBUG ===\n")

# Check critical variables
critical_vars = [
    "BOT_TOKEN",
    "ADMIN_USER_IDS",
    "DATABASE_URL",
    "REDIS_URL",
    "CELERY_BROKER_URL",
    "CELERY_RESULT_BACKEND",
]

for var in critical_vars:
    value = os.getenv(var, "NOT_SET")
    # Mask sensitive values
    if value != "NOT_SET" and var == "BOT_TOKEN":
        display_value = f"{value[:10]}...{value[-5:]}" if len(value) > 15 else "***"
    elif value != "NOT_SET" and "URL" in var:
        # Show just the protocol and host
        display_value = value.split("@")[-1] if "@" in value else value[:30]
    else:
        display_value = value

    print(f"{var}: {display_value}")

print("\n=== ALL ENV VARS (Railway injected) ===\n")
railway_vars = {k: v for k, v in os.environ.items() if k.startswith(("DATABASE", "REDIS", "POSTGRES", "RAILWAY"))}
for k, v in sorted(railway_vars.items()):
    print(f"{k}: {v[:50]}..." if len(v) > 50 else f"{k}: {v}")

print("\n=== END DEBUG ===\n")
