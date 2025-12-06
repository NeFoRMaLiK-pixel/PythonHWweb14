import pytest
from sqlalchemy import inspect

def test_tables_exist(setup_test_database):
    """Проверяем что таблицы создаются."""
    from tests.conftest import test_engine  # ✅ ИСПРАВЛЕНО
    inspector = inspect(test_engine)
    tables = inspector.get_table_names()
    print(f"Available tables: {tables}")
    assert "users" in tables
    assert "contacts" in tables