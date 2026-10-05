"""
Snowflake Agent Deployment Script - Deploy All SQL Files
"""

import os
import glob
import subprocess
from datetime import datetime
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

class C:
    OKGREEN = '\033[92m'
    FAIL = '\033[91m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'

def load_config():
    """Load configuration from .env"""
    config = {
        'account': os.getenv('SNOWFLAKE_ACCOUNT'),
        'user': os.getenv('SNOWFLAKE_USER'),
        'password': os.getenv('SNOWFLAKE_PASSWORD'),
        'database': os.getenv('SNOWFLAKE_DATABASE'),
        'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE'),
    }
    
    required = ['account', 'user', 'password', 'database', 'warehouse']
    for field in required:
        if not config[field]:
            print(f"{C.FAIL}❌ Missing {field} in .env file{C.ENDC}")
            exit(1)
    
    return config

def get_sql_files():
    """Get all SQL files from sql/ directory sorted by filename"""
    sql_files = sorted(glob.glob('sql/*.sql'))
    
    if not sql_files:
        print(f"{C.FAIL}❌ No SQL files found in sql/ directory{C.ENDC}")
        exit(1)
    
    return sql_files

def display_header(config, sql_files):
    """Display deployment header"""
    print(f"\n{C.BOLD}")
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║       SNOWFLAKE NATIVE AGENT - DEPLOYMENT                     ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    print(f"{C.ENDC}\n")
    
    print(f"{C.BOLD}Snowflake Details:{C.ENDC}")
    print(f"  Account:   {C.OKGREEN}{config['account']}{C.ENDC}")
    print(f"  User:      {C.OKGREEN}{config['user']}{C.ENDC}")
    print(f"  Database:  {C.OKGREEN}{config['database']}{C.ENDC}")
    print(f"  Warehouse: {C.OKGREEN}{config['warehouse']}{C.ENDC}")
    
    print(f"\n{C.BOLD}SQL Files to Deploy ({len(sql_files)}):{C.ENDC}")
    for sql_file in sql_files:
        print(f"  ✨ {sql_file}")

def confirm_deployment():
    """Ask user for confirmation"""
    print(f"\n{C.BOLD}⚠️  Proceed with deployment? (yes/no): {C.ENDC}", end="")
    response = input().strip().lower()
    
    if response not in ['yes', 'y']:
        print(f"{C.FAIL}❌ Deployment cancelled{C.ENDC}")
        exit(0)
    
    return True

def connect_snowflake(config):
    """Connect to Snowflake"""
    try:
        print(f"\n{C.BOLD}Connecting to Snowflake...{C.ENDC}")
        conn = snowflake.connector.connect(
            account=config['account'],
            user=config['user'],
            password=config['password'],
            database=config['database'],
            warehouse=config['warehouse']
        )
        print(f"{C.OKGREEN}✅ Connected{C.ENDC}\n")
        return conn
    except Exception as e:
        print(f"{C.FAIL}❌ Connection failed: {e}{C.ENDC}")
        exit(1)

def execute_deployment(conn, cursor, sql_files):
    """Execute all SQL files"""
    print(f"{C.BOLD}Deploying...{C.ENDC}\n")
    
    for sql_file in sql_files:
        try:
            print(f"  ▶️  {sql_file}...")
            with open(sql_file, 'r') as f:
                sql = f.read()
            
            # Split by semicolon and execute each statement
            statements = [s.strip() for s in sql.split(';') if s.strip()]
            
            for statement in statements:
                cursor.execute(statement)
            
            conn.commit()
            print(f"     {C.OKGREEN}✅ Done{C.ENDC}")
        
        except FileNotFoundError:
            print(f"     {C.FAIL}❌ File not found{C.ENDC}")
            exit(1)
        except Exception as e:
            print(f"     {C.FAIL}❌ Error: {e}{C.ENDC}")
            exit(1)
    
    print(f"\n{C.OKGREEN}✅ Deployment completed successfully!{C.ENDC}")

def show_next_steps():
    """Show next steps"""
    print(f"\n{C.BOLD}{'='*65}{C.ENDC}")
    print(f"{C.BOLD}NEXT STEPS:{C.ENDC}")
    print(f"{'='*65}\n")
    
    print(f"1. Open Snowflake Console:")
    print(f"   {C.OKGREEN}https://app.snowflake.com/{C.ENDC}")
    
    print(f"\n2. Go to Intelligence/Copilot")
    
    print(f"\n3. Ask questions directly to the agent:")
    print(f"   • Show me top 10 customers by revenue")
    print(f"   • Which sales reps are underperforming?")
    print(f"   • What products are trending?")
    print(f"   • Show high churn risk customers")
    print(f"   • Show inventory alerts")
    print(f"   • Customer lifetime value analysis")
    
    print(f"\n4. Push to GitHub:")
    print(f"   {C.OKGREEN}.\push-to-github.ps1{C.ENDC}")
    
    print(f"\n{C.BOLD}{'='*65}{C.ENDC}\n")

def main():
    """Main execution"""
    sql_files = get_sql_files()
    config = load_config()
    display_header(config, sql_files)
    confirm_deployment()
    
    conn = connect_snowflake(config)
    cursor = conn.cursor()
    execute_deployment(conn, cursor, sql_files)
    
    cursor.close()
    conn.close()
    
    show_next_steps()

if __name__ == '__main__':
    main()