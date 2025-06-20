import os
import sqlite3

class DataManager:
    """
    A class to manage SQLite database connections and operations.

    Attributes:
        file_locator (str): Path to the SQLite database file.
        readonly (bool): Flag to indicate if the database should be opened in read-only mode.
    """

    def __init__(self, file_locator: str, readonly: bool = False) -> None:
        """
        Initializes the DataManager with the database file path and mode.

        Args:
            file_locator (str): Path to the SQLite database file.
            readonly (bool): Flag to indicate if the database should be opened in read-only mode.
        """
        self.data_connection = None
        self.file_locator = file_locator
        self.readonly = readonly

    def get_db_connection(self) -> sqlite3.Connection:
        """
        Establishes and returns a connection to the SQLite database.

        Returns:
            sqlite3.Connection: A connection object to the SQLite database.

        Raises:
            ValueError: If the database path is not set or empty.
            FileNotFoundError: If the database file does not exist.
        """
        # Retrieve the database file path from the environment variable
        db_path = self.file_locator

        if db_path.lower() == ":memory:":
            return sqlite3.connect(db_path.lower())
        
        if not db_path:
            raise ValueError("Environment variable MIMICIV_DB_PATH is not set or empty.")
        # Connect to the local SQLite database

        db_path = os.path.realpath(db_path)

        if not os.path.exists(db_path):
            raise FileNotFoundError(f"File {db_path} does not exist")
        
        mode = "ro" if self.readonly else "rw"
        conn = sqlite3.connect(f"file:{db_path}?mode={mode}", uri=True)
        # Ensure rows are returned as tuples rather than strings
        conn.row_factory = sqlite3.Row
        return conn

    def execute_sql(self, sql_query: str = None) -> list[dict]:
        """
        Executes an SQL query and returns the results as a list of dictionaries.

        Args:
            sql_query (str): The SQL query to execute.

        Returns:
            list[dict]: A list of dictionaries representing the query results, 
                        where each dictionary maps column names to their values.
        """
        cursor = self.data_connection.cursor()
        self.data_connection.row_factory = sqlite3.Row 
        cursor.execute(sql_query)
        
        # Retrieve column names to build a list of dict objects
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return results

    def __enter__(self):
        """
        Context manager entry method. Opens the database connection.

        Returns:
            DataManager: The current instance of the DataManager.
        """
        self.data_connection = self.get_db_connection()
        return self
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        """
        Context manager exit method. Closes the database connection.

        Args:
            exc_type (type): The exception type, if any.
            exc_value (Exception): The exception instance, if any.
            exc_traceback (traceback): The traceback object, if any.

        Raises:
            Exception: Re-raises any exception that occurred within the context.
        """
        self.data_connection.close()        
        if exc_type:
            raise exc_type(exc_value)

