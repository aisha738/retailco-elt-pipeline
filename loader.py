import os
import logging
import psycopg2
import dlt
from dotenv import load_dotenv

# Load our passwords from the hidden vault
load_dotenv()

# Configure logging so we can track the pipeline's progress
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Build the secure connection string for dlt to access the Data Warehouse (Port 5434)
DWH_URL = f"postgresql://{os.environ.get('DWH_USER')}:{os.environ.get('DWH_PASS')}@{os.environ.get('DWH_HOST')}:{os.environ.get('DWH_PORT')}/{os.environ.get('DWH_NAME')}"

# The complete list of entities we need to move from the Lake to the Warehouse
ENDPOINTS = [
    "customers", 
    "products", 
    "stores", 
    "employees", 
    "payment_methods", 
    "orders", 
    "payments", 
    "inventory_movements"
]

def get_lake_connection():
    """
    Establishes a connection to our raw Data Lake (Port 5433).
    We use this to read the raw JSON payloads we saved during extraction.
    """
    return psycopg2.connect(
        host=os.environ.get("DB_HOST"),
        port=os.environ.get("DB_PORT"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASS"),
        dbname=os.environ.get("DB_NAME")
    )

def fetch_raw_data(table_name):
    """
    A Python generator that reaches into the Data Lake, pulls out the raw JSON payload,
    and yields it one row at a time. Using 'yield' prevents us from loading millions 
    of rows into your computer's RAM all at once.
    """
    conn = get_lake_connection()
    try:
        with conn.cursor() as cur:
            # We only select the 'payload' column because it contains the full JSON dictionary
            cur.execute(f"SELECT payload FROM raw.{table_name};")
            for row in cur:
                yield row[0] # Yields the JSON dictionary to dlt
    except Exception as e:
        logger.error(f"Error reading from raw.{table_name}: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("\n--- Starting Full dlt Warehouse Load ---")
    
    # 1. Initialize the dlt pipeline
    # We define the destination (Postgres) and the schema name ('analytics')
    pipeline = dlt.pipeline(
        pipeline_name='retailco_warehouse_pipeline',
        destination=dlt.destinations.postgres(credentials=DWH_URL),
        dataset_name='analytics' 
    )
    
    # 2. Loop through every entity and process it
    for endpoint in ENDPOINTS:
        print(f"\nExtracting '{endpoint}' from Lake and loading to Warehouse...")
        
        try:
            # The pipeline.run command handles table creation, schema evolution, and inserts
            load_info = pipeline.run(
                fetch_raw_data(endpoint),
                table_name=endpoint,
                write_disposition="merge", # "merge" means Upsert (idempotent updates)
                primary_key="id"
            )
            logger.info(f"SUCCESS: {endpoint} securely loaded to the Data Warehouse.")
        except Exception as e:
            logger.error(f"Failed to load {endpoint}: {e}")
            
    print("\n--- CHECKPOINT 3 COMPLETE: All tables loaded into the Analytics Warehouse! ---")