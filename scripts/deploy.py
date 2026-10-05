```python
"""
Snowflake Agent Deployment Script - Deploy All SQL Files

Auto-deploy in CI/CD environments (GitHub Actions)
"""

import os
import glob
import sys
from datetime import datetime

import snowflake.connector
from dotenv import load_dotenv

load_dotenv()


class C:
    OKGREEN = '\033[92m'
    FAIL = '\033[91m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'


def is_ci_environment():
    """Check if running in CI/CD environment."""
    return (
        os.getenv('GITHUB_ACTIONS') == 'true'
        or os.getenv('CI') == 'true'
    )


def load_config():
    """Load configuration from environment variables."""
    config = {
        'account': os.getenv('SNOWFLAKE_ACCOUNT'),
        'user': os.getenv('SNOWFLAKE_USER'),
        'password': os.getenv('SNOWFLAKE_PASSWORD'),
        'database': os.getenv('SNOWFLAKE_DATABASE'),
        'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE'),
    }

    required = [
        'account',
        'user',
        'password',
        'database',
        'warehouse'
    ]

    for field in required:
        if not config[field]:
            print(
                f"{C.FAIL}❌ Missing {field} in environment variables{C.ENDC}"
            )
            sys.exit(1)

    return config


def get_sql_files():
    """Get all SQL files from sql/ directory sorted by filename."""
    sql_files = sorted(glob.glob('sql/*.sql'))

    if not sql_files:
        print(
            f"{C.FAIL}❌ No SQL files found in sql/ directory{C.ENDC}"
        )
        sys.exit(1)

    return sql_files


def display_header(config, sql_files):
    """Display deployment header."""
    print(f"\n{C.BOLD}")
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║       SNOWFLAKE NATIVE AGENT - DEPLOYMENT                    ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    print(f"{C.ENDC}\n")

    print(f"{C.BOLD}Snowflake Details:{C.ENDC}")
    print(f"  Account:   {C.OKGREEN}{config['account']}{C.ENDC}")
    print(f"  User:      {C.OKGREEN}{config['user']}{C.ENDC}")
    print(f"  Database:  {C.OKGREEN}{config['database']}{C.ENDC}")
    print(f"  Warehouse: {C.OKGREEN}{config['warehouse']}{C.ENDC}")

    if is_ci_environment():
        print(
            f"\n{C.BOLD}Environment: "
            f"{C.OKGREEN}GitHub Actions (Auto-deploy){C.ENDC}"
        )
    else:
        print(
            f"\n{C.BOLD}Environment: "
            f"{C.OKGREEN}Local (Interactive){C.ENDC}"
        )

    print(f"\n{C.BOLD}SQL Files to Deploy ({len(sql_files)}):{C.ENDC}")

    for sql_file in sql_files:
        print(f"  ✨ {sql_file}")


def confirm_deployment():
    """Ask user for confirmation (skip in CI/CD)."""
    if is_ci_environment():
        print(
            f"\n{C.BOLD}"
            f"Auto-deploying in CI/CD environment..."
            f"{C.ENDC}\n"
        )
        return True

    print(
        f"\n{C.BOLD}⚠️  Proceed with deployment? (yes/no): "
        f"{C.ENDC}",
        end=""
    )

    response = input().strip().lower()

    if response not in ['yes', 'y']:
        print(f"{C.FAIL}❌ Deployment cancelled{C.ENDC}")
        sys.exit(0)

    return True


def connect_snowflake(config):
    """Connect to Snowflake."""
    try:
        print(f"{C.BOLD}Connecting to Snowflake...{C.ENDC}")

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
        print(
            f"{C.FAIL}❌ Connection failed: {e}{C.ENDC}"
        )
        sys.exit(1)


def split_sql_statements(sql):
    """
    Split SQL into individual statements while preserving
    Snowflake $$ ... $$ blocks.

    IMPORTANT:
    Do NOT simply use sql.split(';') because Snowflake
    stored procedures and Cortex Agent specifications can
    contain semicolons inside $$ ... $$ blocks.
    """

    statements = []

    current = []
    inside_dollar_block = False
    i = 0

    while i < len(sql):

        # Detect Snowflake $$ delimiter.
        if sql[i:i + 2] == '$$':
            current.append('$$')
            inside_dollar_block = not inside_dollar_block
            i += 2
            continue

        char = sql[i]

        # Semicolon outside $$ block = end of SQL statement.
        if char == ';' and not inside_dollar_block:
            statement = ''.join(current).strip()

            if statement:
                statements.append(statement)

            current = []
            i += 1
            continue

        current.append(char)
        i += 1

    # Add final statement if there is no semicolon.
    final_statement = ''.join(current).strip()

    if final_statement:
        statements.append(final_statement)

    if inside_dollar_block:
        raise ValueError(
            "Unclosed $$ block detected in SQL file. "
            "Check the $$ delimiters."
        )

    return statements


def execute_deployment(conn, cursor, sql_files):
    """Execute all SQL files."""

    print(f"{C.BOLD}Deploying...{C.ENDC}\n")

    for sql_file in sql_files:

        try:
            print(f"  ▶️  {sql_file}...")

            with open(sql_file, 'r', encoding='utf-8') as f:
                sql = f.read()

            statements = split_sql_statements(sql)

            print(
                f"     Found {len(statements)} SQL statement(s)"
            )

            for index, statement in enumerate(statements, start=1):

                # Ignore empty statements.
                if not statement.strip():
                    continue

                print(
                    f"     Executing statement "
                    f"{index}/{len(statements)}..."
                )

                cursor.execute(statement)

            conn.commit()

            print(
                f"     {C.OKGREEN}✅ Done{C.ENDC}"
            )

        except FileNotFoundError:
            print(
                f"     {C.FAIL}❌ File not found{C.ENDC}"
            )
            sys.exit(1)

        except Exception as e:
            print(
                f"     {C.FAIL}❌ Error: {e}{C.ENDC}"
            )
            conn.rollback()
            sys.exit(1)

    print(
        f"\n{C.OKGREEN}"
        f"✅ All SQL files deployed successfully!"
        f"{C.ENDC}"
    )


def show_next_steps():
    """Show next steps."""

    print(
        f"\n{C.BOLD}"
        f"{'=' * 65}"
        f"{C.ENDC}"
    )

    print(
        f"{C.BOLD}"
        f"✅ DEPLOYMENT COMPLETE"
        f"{C.ENDC}"
    )

    print(
        f"{C.BOLD}"
        f"{'=' * 65}"
        f"{C.ENDC}\n"
    )

    print(
        f"{C.BOLD}"
        f"Agent is ready in Snowflake Intelligence!"
        f"{C.ENDC}\n"
    )

    print("1. Open Snowflake Console:")
    print(
        f"   {C.OKGREEN}"
        f"https://app.snowflake.com/"
        f"{C.ENDC}\n"
    )

    print("2. Go to Intelligence/Copilot section\n")

    print("3. Ask questions to SNOWFLAKE_DATA_AGENT:")
    print("   • Show me top 10 customers by revenue")
    print("   • Which sales reps are underperforming?")
    print("   • What products are trending?")
    print("   • Show high churn risk customers")
    print("   • Show inventory alerts")
    print("   • Customer lifetime value analysis\n")

    if not is_ci_environment():
        print("4. Push to GitHub:")
        print(
            f"   {C.OKGREEN}"
            f".\\push-to-github.ps1"
            f"{C.ENDC}\n"
        )

    print(
        f"{C.BOLD}"
        f"{'=' * 65}"
        f"{C.ENDC}\n"
    )


def main():
    """Main execution."""

    sql_files = get_sql_files()

    config = load_config()

    display_header(config, sql_files)

    confirm_deployment()

    conn = connect_snowflake(config)

    cursor = conn.cursor()

    try:
        execute_deployment(
            conn,
            cursor,
            sql_files
        )
    finally:
        cursor.close()
        conn.close()

    show_next_steps()


if __name__ == '__main__':
    main()
```
