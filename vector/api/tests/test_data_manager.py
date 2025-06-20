import pytest
import sqlite3
import tempfile
import os
from api.services import DataManager


@pytest.fixture
def temp_db():
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db_path = temp_db.name
    temp_db.close()

    conn = sqlite3.connect(temp_db_path)
    conn.execute('CREATE TABLE patients (subject_id INTEGER PRIMARY KEY, name TEXT)')
    conn.execute('INSERT INTO patients (subject_id, name) VALUES (10000001, "John Doe")')
    conn.commit()
    conn.close()

    yield temp_db_path

    os.unlink(temp_db_path)


def test_db_connection_success(temp_db):
    with DataManager(file_locator=temp_db) as data_manager:
        conn = data_manager.get_db_connection()
        assert isinstance(conn, sqlite3.Connection)


def test_db_connection_failure():
    with pytest.raises(FileNotFoundError):
        with DataManager(file_locator='nonexistent.db') as data_manager:
            data_manager.get_db_connection()


def test_execute_sql_success(temp_db):
    with DataManager(file_locator=temp_db) as data_manager:
        result = data_manager.execute_sql("SELECT * FROM patients")
        expected = [{'subject_id': 10000001, 'name': 'John Doe'}]
        assert result == expected


def test_execute_sql_invalid_query(temp_db):
    with pytest.raises(sqlite3.OperationalError):
        with DataManager(file_locator=temp_db) as data_manager:
            data_manager.execute_sql("SELECT invalid_column FROM patients")
