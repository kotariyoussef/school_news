import psycopg2
from urllib.parse import urlparse
from psycopg2 import OperationalError

# Your database URL
db_url = "postgresql://postgres:XBtpORxNFOsyIVPABoijLDJrlEnphWGZ@shortline.proxy.rlwy.net:40176/railway"

try:
    # Parse the URL
    url = urlparse(db_url)

    # Extract the components of the URL
    dbname = url.path[1:]
    user = url.username
    password = url.password
    host = url.hostname
    port = url.port

    # Establish the connection
    conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )

    # Create a cursor object
    cur = conn.cursor()

    # Execute a query to test the connection
    cur.execute("SELECT version();")
    db_version = cur.fetchone()
    print(f"PostgreSQL version: {db_version}")

except OperationalError as e:
    print(f"Error connecting to the database: {e}")
finally:
    # Close the cursor and connection
    if cur:
        cur.close()
    if conn:
        conn.close()
