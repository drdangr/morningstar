import os
import pytest

@pytest.fixture(autouse=True)
def set_admin_telegram_id():
    if 'ADMIN_TELEGRAM_ID' not in os.environ:
        os.environ['ADMIN_TELEGRAM_ID'] = '123456789'  # Set a default value for testing purposes
    yield
    del os.environ['ADMIN_TELEGRAM_ID']  # Clean up after tests