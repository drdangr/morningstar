ADMIN_TELEGRAM_ID = os.getenv('ADMIN_TELEGRAM_ID')
if ADMIN_TELEGRAM_ID is None:
    raise ValueError("Environment variable 'ADMIN_TELEGRAM_ID' is not set.")
ADMIN_ID = int(ADMIN_TELEGRAM_ID)