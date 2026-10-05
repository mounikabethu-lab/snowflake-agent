"""
Snowflake Agent Deployment Script
"""

import os
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

# Get Snowflake credentials
account = os.getenv('SNOWFLAKE_ACCOUNT')
user = os.getenv('SNOWFLAKE_USER')
password = os.getenv('SNOWFLAKE_PASSWORD')
database = os.getenv('SNOWFLAKE_DATABASE')
warehouse = os.getenv('SNOWFLAKE_WAREHOUSE')

print("=" * 65)
print("SNOWFLAKE NATIVE AGENT - DEPLOYMENT")
print("=" * 65)
print()

print("Snowflake Details:")
print(f"  Account:   {account}")
print(f"  User:      {user}")
print(f"  Database:  {database}")
print(f"  Warehouse: {warehouse}")
print()

try:
    # Connect to Snowflake
    print("Connecting to Snowflake...")
    conn = snowflake.connector.connect(
        account=account,
        user=user,
        password=password,
        database=database,
        warehouse=warehouse
    )
    print("✅ Connected")
    print()
    
    cursor = conn.cursor()
    
    # Execute SQL files
    sql_files = [
        'sql/01_create_semantic_layer.sql',
        'sql/02_create_agent.sql',
        'sql/03_set_agent_instructions.sql',
        'sql/04_create_knowledge_base.sql',
        'sql/05_deploy.sql'
    ]
    
    print("Deploying...")
    print()
    
    for sql_file in sql_files:
        print(f"  ▶️  {sql_file}...")
        
        try:
            with open(sql_file, 'r') as f:
                sql_content = f.read()
            
            # Execute using execute_string for multiple statements
            cursor.execute_string(sql_content)
            
            print(f"     ✅ Done")
            
        except Exception as e:
            print(f"     ❌ Error: {e}")
            raise
    
    print()
    print("✅ Deployment completed successfully!")
    print()
    
    cursor.close()
    conn.close()

except FileNotFoundError as e:
    print(f"❌ File not found: {e}")
    exit(1)
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)