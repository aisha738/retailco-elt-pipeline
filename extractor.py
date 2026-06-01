import os
import time
import logging
import requests
import json
import psycopg2
import psycopg2.extras
import datetime
from dotenv import load_dotenv

# Load environment variables from the local .env file securely
load_dotenv()

# Configure logging to output timestamped, informative messages to the terminal
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Base configuration for the API
API_BASE_URL = "https://hngstage8da-55c7f5f769c8.herokuapp.com"
API_KEY = os.environ.get("API_KEY")

# The complete list of API endpoints required for the Data Warehouse extraction
ENDPOINTS = [
    "customers", 
    "products", 
    "stores", 
    "employees", 
    "payment_methods", 
    "orders", 
    "order_items",  # <--- Added this missing endpoint
    "payments", 
    "inventory_movements"
]

# Fail fast if the API key is missing to prevent unauthorized requests
if not API_KEY:
    raise ValueError("No API_KEY found. Please check your .env file.")

def get_db_connection():
    """
    Establishes and returns a connection to the PostgreSQL database
    using credentials stored in the environment variables.
    """
    return psycopg2.connect(
        host=os.environ.get("DB_HOST"),
        port=os.environ.get("DB_PORT"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASS"),
        dbname=os.environ.get("DB_NAME")
    )

def make_robust_request(url, params=None, max_retries=5):
    """
    Executes an HTTP GET request with built-in resilience.
    Handles rate limiting (429), server errors (5xx), and network drops
    using an exponential backoff strategy.
    """
    headers = {"X-API-Key": API_KEY}
    attempt = 0
    backoff_factor = 2 # Multiplier for increasing wait time between retries

    while attempt < max_retries:
        try:
            # 10-second timeout prevents the script from hanging indefinitely
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            # Request successful
            if response.status_code == 200:
                return response.json()
            
            # Handle API rate limiting
            elif response.status_code == 429:
                # Use the API's suggested wait time if provided, otherwise use exponential backoff
                retry_after = int(response.headers.get("Retry-After", backoff_factor ** attempt))
                logger.warning(f"Rate limited. Retrying in {retry_after}s...")
                time.sleep(retry_after)
                attempt += 1
                
            # Handle temporary server-side crashes/maintenance
            elif response.status_code >= 500:
                sleep_time = backoff_factor ** attempt
                logger.warning(f"Server error {response.status_code}. Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
                attempt += 1
                
            # Handle client-side errors (e.g., 401 Unauthorized, 404 Not Found)
            else:
                logger.error(f"Failed request: {response.status_code} - {response.text}")
                response.raise_for_status()
                
        # Catch network interruptions
        except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
            sleep_time = backoff_factor ** attempt
            logger.warning(f"Network error: {e}. Retrying in {sleep_time}s...")
            time.sleep(sleep_time)
            attempt += 1
            
    raise Exception(f"Max retries exceeded for URL: {url}")

def fetch_all_pages(endpoint, updated_after=None):
    """
    Loops through an API endpoint to fetch all available records using cursor-based pagination.
    Supports incremental loading if an 'updated_after' timestamp is provided.
    """
    url = f"{API_BASE_URL}/{endpoint}"
    all_data = []
    
    # Initialize query parameters
    params = {}
    if updated_after:
        params["updated_after"] = updated_after
        
    has_more = True
    
    logger.info(f"Starting extraction for /{endpoint}...")
    while has_more:
        # Fetch the current page
        response_data = make_robust_request(url, params=params)
        records = response_data.get("data", [])
        all_data.extend(records)
        
        # Check API metadata to see if more pages exist
        meta = response_data.get("meta", {})
        has_more = meta.get("has_more", False)
        
        # Update the cursor for the next iteration
        if has_more and meta.get("cursor"):
            params["cursor"] = meta.get("cursor")
        else:
            break

    logger.info(f"Finished /{endpoint}. Total records: {len(all_data)}")
    return all_data

def setup_database(conn):
    """
    Prepares the PostgreSQL environment.
    Creates the 'raw' schema and the '_watermarks' state table if they do not exist.
    """
    with conn.cursor() as cur:
        cur.execute("CREATE SCHEMA IF NOT EXISTS raw;")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS raw._watermarks (
                endpoint VARCHAR PRIMARY KEY,
                last_updated_at TIMESTAMP
            );
        """)
        conn.commit()

def get_watermark(conn, endpoint):
    """
    Retrieves the most recent updated_at timestamp for a specific endpoint.
    Used to determine where the last extraction run left off.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT last_updated_at FROM raw._watermarks WHERE endpoint = %s;", (endpoint,))
        result = cur.fetchone()
        # Return as an ISO 8601 string if a watermark exists
        return result[0].isoformat() if result else None

def save_to_lake(conn, endpoint, data):
    """
    Writes extracted API data to the raw schema using an idempotent UPSERT strategy.
    Saves the full JSON payload for flexibility, then updates the watermark.
    """
    if not data:
        logger.info(f"No new data to save for {endpoint}.")
        return

    with conn.cursor() as cur:
        # Dynamically create a destination table for the endpoint
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS raw.{endpoint} (
                id VARCHAR PRIMARY KEY,
                payload JSONB,
                updated_at TIMESTAMP
            );
        """)
        
        records = []
        # Set a baseline timestamp to compare against incoming records
        max_updated_at = "1970-01-01T00:00:00"
        
        for item in data:
            record_id = str(item.get("id"))
            # Prioritize updated_at, fallback to created_at if missing
            updated_at = item.get("updated_at") or item.get("created_at")
            
            # Serialize the dictionary back into a JSON string for the database
            payload_json = json.dumps(item)
            records.append((record_id, payload_json, updated_at))
            
            # Track the highest timestamp in this batch to serve as the new watermark
            if updated_at and updated_at > max_updated_at:
                max_updated_at = updated_at

        # Safety Net: If the API records lacked any timestamps, default the watermark 
        # to the current execution time to prevent perpetual full-table scans.
        if max_updated_at == "1970-01-01T00:00:00":
            max_updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Perform a bulk UPSERT using execute_values for performance.
        # ON CONFLICT guarantees idempotency (prevents duplicate rows on rerun).
        psycopg2.extras.execute_values(
            cur,
            f"""
            INSERT INTO raw.{endpoint} (id, payload, updated_at)
            VALUES %s
            ON CONFLICT (id) DO UPDATE SET
                payload = EXCLUDED.payload,
                updated_at = EXCLUDED.updated_at;
            """,
            records
        )
        
        # Update the metadata table so the next run knows where to start
        cur.execute("""
            INSERT INTO raw._watermarks (endpoint, last_updated_at)
            VALUES (%s, %s)
            ON CONFLICT (endpoint) DO UPDATE SET
                last_updated_at = EXCLUDED.last_updated_at;
        """, (endpoint, max_updated_at))
        
        conn.commit()
        logger.info(f"Successfully saved {len(records)} records to raw.{endpoint}")
        logger.info(f"Watermark for {endpoint} updated to {max_updated_at}")

if __name__ == "__main__":
    print("\n--- Starting Full Lake Extraction ---")
    conn = get_db_connection()
    
    try:
        # Ensure foundational database structures are in place
        setup_database(conn)
        
        # Iterate through all required entities to populate the lake
        for endpoint in ENDPOINTS:
            print(f"\n--- Processing {endpoint} ---")
            
            # Check history to decide between incremental or full load
            last_run_time = get_watermark(conn, endpoint)
            
            if last_run_time:
                logger.info(f"Incremental run: Fetching data updated after {last_run_time}")
            else:
                logger.info("First run: Performing full historical extract.")
            
            # Extract and Load
            new_data = fetch_all_pages(endpoint, updated_after=last_run_time)
            save_to_lake(conn, endpoint, new_data)
            
        print("\nSUCCESS: All entities safely written to the Data Lake!")
        
    finally:
        # Ensure the database connection is cleanly closed even if the script crashes
        conn.close()