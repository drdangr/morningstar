def test_admin_telegram_id():
    import os
    import pytest

    admin_telegram_id = os.getenv('ADMIN_TELEGRAM_ID')
    if admin_telegram_id is None:
        pytest.fail("Environment variable ADMIN_TELEGRAM_ID is not set")
    
    admin_telegram_id = int(admin_telegram_id)
    assert isinstance(admin_telegram_id, int)