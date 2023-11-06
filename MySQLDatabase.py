import mysql.connector
from sshtunnel import SSHTunnelForwarder



class MySQLDatabase:
    def __init__(self, host, username, password, database, ssh_host, ssh_port, ssh_user, ssh_password):
        self.ssh_host = ssh_host
        self.ssh_port = ssh_port
        self.ssh_user = ssh_user
        self.ssh_password = ssh_password
        self.host = host
        self.username = username
        self.password = password
        self.database = database

    def establish_ssh_tunnel(self):
        # Create the SSH tunnel
        with SSHTunnelForwarder(
            (self.ssh_host, self.ssh_port),
            ssh_username=self.ssh_user,
            ssh_password=self.ssh_password,
            remote_bind_address=(self.host, 3306)  # Use the correct MySQL port here
        ) as tunnel:
            if tunnel.is_active:
                print("SSH tunnel successfully created.")
                self._configure_mysql_connection()

    def _configure_mysql_connection(self):
        try:
            self.connection = mysql.connector.connect(
                host='127.0.0.1',  # Use '127.0.0.1' for SSH tunnel
                user=self.username,
                password=self.password,
                database=self.database
            )
            self.cursor = self.connection.cursor(dictionary=True)
        except Exception as e:
            raise Exception(f"Error connecting to the database: {str(e)}")

    def close(self):
        """
        Closes the MySQL database connection.
        """
        self.cursor.close()
        self.connection.close()


    def execute_query(self, query, params=None):
        """
        Executes a SQL query on the MySQL database.

        Args:
            query (str): The SQL query to execute.
            params (tuple, optional): Parameters to be used in the query.

        Returns:
            list: The result of the query as a list of dictionaries.
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            self.connection.rollback()
            raise Exception(f"Error executing query: {str(e)}")

    def insert_data(self, query, data):
        """
        Inserts data into the MySQL database.

        Args:
            query (str): The SQL insert query.
            data (tuple): Data to be inserted into the database.

        Returns:
            None
        """
        try:
            self.cursor.execute(query, data)
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise Exception(f"Error inserting data: {str(e)}")

    def update_data(self, query, data):
        """
        Updates data in the MySQL database.

        Args:
            query (str): The SQL update query.
            data (tuple): Data to be updated in the database.

        Returns:
            None
        """
        try:
            self.cursor.execute(query, data)
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise Exception(f"Error updating data: {str(e)}")

    def delete_data(self, query, data):
        """
        Deletes data from the MySQL database.

        Args:
            query (str): The SQL delete query.
            data (tuple): Data to be used in the query.

        Returns:
            None
        """
        try:
            self.cursor.execute(query, data)
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise Exception(f"Error deleting data: {str(e)}")
