import os
import pandas as pd
import xarray as xr
from dotenv import load_dotenv
from sqlalchemy import (create_engine, inspect, MetaData, Table, Column, 
                        Integer, Float, DateTime, String)
from geoalchemy2.types import Geometry # type: ignore
import warnings

# Suppress pandas warning
warnings.filterwarnings("ignore", category=FutureWarning)

# --- 1. SETUP AND DATABASE CONNECTION ---
load_dotenv()
db_url = os.getenv("DATABASE_URL")
if not db_url:
    raise Exception("DATABASE_URL not found in .env file")

engine = create_engine(db_url)
metadata = MetaData()

# --- 2. DEFINE THE DATABASE TABLE STRUCTURE ---
argo_table = Table('argo_measurements', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('float_id', String(20)),
    Column('timestamp', DateTime),
    Column('latitude', Float),
    Column('longitude', Float),
    Column('pressure', Float),
    Column('temperature', Float),
    Column('salinity', Float),
    Column('location', Geometry('POINT', srid=4326)) # For geospatial queries
)

# --- 3. PARSE THE NETCDF FILE ---
def parse_argo_file(file_path):
    print(f"Opening NetCDF file: {file_path}")
    try:
        with xr.open_dataset(file_path) as ds:
            # Extract the platform number (float ID)
            platform_number = ds.PLATFORM_NUMBER.values[0].decode('utf-8').strip()
            
            # Convert to a pandas DataFrame for easier handling
            df = ds.to_dataframe().reset_index()
            
            # Select and rename columns for clarity
            core_data = df[[
                'JULD', 'LATITUDE', 'LONGITUDE', 
                'PRES_ADJUSTED', 'TEMP_ADJUSTED', 'PSAL_ADJUSTED'
            ]].copy()
            core_data.rename(columns={
                'JULD': 'timestamp',
                'LATITUDE': 'latitude',
                'LONGITUDE': 'longitude',
                'PRES_ADJUSTED': 'pressure',
                'TEMP_ADJUSTED': 'temperature',
                'PSAL_ADJUSTED': 'salinity'
            }, inplace=True)

            
            # Add the float ID to each row
            core_data['float_id'] = platform_number

            # Drop rows with any missing measurements
            core_data.dropna(inplace=True)
            
            print(f"Successfully parsed {len(core_data)} measurements for float {platform_number}")
            return core_data

    except Exception as e:
        print(f"Error parsing file {file_path}: {e}")
        return None

# --- 4. MAIN EXECUTION LOGIC ---
if __name__ == "__main__":
    try:
        # Check if the table exists, and create it if it doesn't
        inspector = inspect(engine)
        if not inspector.has_table('argo_measurements'):
            print("Table 'argo_measurements' not found. Creating table...")
            metadata.create_all(engine)
            print("Table created successfully.")
        else:
            print("Table 'argo_measurements' already exists.")

        # Parse the data file
        file_path = os.path.join('data', 'R2902347_001.nc')
        argo_data = parse_argo_file(file_path)

        if argo_data is not None and not argo_data.empty:
            with engine.connect() as connection:
                # Begin a transaction
                with connection.begin() as transaction:
                    # Check for existing data from this float and timestamp
                    first_timestamp = argo_data['timestamp'].min()
                    float_id = argo_data['float_id'].iloc[0]
                    
                    from sqlalchemy import text
                    result = connection.execute(
                        text("SELECT COUNT(*) FROM argo_measurements WHERE float_id = :fid AND timestamp >= :ts"),
                        {'fid': float_id, 'ts': first_timestamp}
                    ).scalar()

                    if result > 0:
                        print(f"Data for float {float_id} from this profile already exists. Skipping insertion.")
                    else:
                        print(f"Inserting {len(argo_data)} new records into the database...")
                        # Prepare data for insertion, including the PostGIS location point
                        records_to_insert = []
                        for index, row in argo_data.iterrows():
                            record = row.to_dict()
                            record['location'] = f"POINT({row['longitude']} {row['latitude']})"
                            records_to_insert.append(record)
                        
                        # Use the Core API for efficient bulk insertion
                        connection.execute(argo_table.insert(), records_to_insert)
                        print("✅ Data insertion complete.")
                
    except Exception as e:
        print(f"An error occurred during the ingestion process: {e}")