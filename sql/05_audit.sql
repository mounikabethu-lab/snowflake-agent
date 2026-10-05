"""
Snowflake Agent Deployment Script
Deploy all SQL files from the sql/ directory.
"""

import os
import glob
import sys

import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

def is_ci_environment():
return (
os.getenv("GITHUB_ACTIONS") == "true"
or os.getenv("CI") == "true"
)

def load_config():
config = {
"account": os.getenv("SNOWFLAKE_ACCOUNT"),
"user": os.getenv("SNOWFLAKE_USER"),
"password": os.getenv("SNOWFLAKE_PASSWORD"),
"database": os.getenv("SNOWFLAKE_DATABASE"),
"warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
}

```
required = [
    "account",
    "user",
    "password",
    "database",
    "warehouse",
]

for field in required:
    if not config[field]:
        print(f"ERROR: Missing {field}")
        sys.exit(1)

return config
```

def get_sql_files():
sql_files = sorted(glob.glob("sql/*.sql"))

```
if not sql_files:
    print("ERROR: No SQL files found in sql/")
    sys.exit(1)

return sql_files
```

def connect_snowflake(config):
print("Connecting to Snowflake...")

```
try:
    conn = snowflake.connector.connect(
        account=config["account"],
        user=config["user"],
        password=config["password"],
        database=config["database"],
        warehouse=config["warehouse"],
    )

    print("Connected successfully.")
    return conn

except Exception as e:
    print(f"ERROR: Connection failed: {e}")
    sys.exit(1)
```

def split_sql_statements(sql):
"""
Split SQL statements while preserving \(...\) blocks.

```
Semicolons inside a $$ block are NOT treated as
statement separators.
"""

statements = []
current = []

inside_dollar_block = False
i = 0

while i < len(sql):

    if sql[i:i + 2] == "$$":
        current.append("$$")
        inside_dollar_block = not inside_dollar_block
        i += 2
        continue

    char = sql[i]

    if char == ";" and not inside_dollar_block:
        statement = "".join(current).strip()

        if statement:
            statements.append(statement)

        current = []
        i += 1
        continue

    current.append(char)
    i += 1

final_statement = "".join(current).strip()

if final_statement:
    statements.append(final_statement)

if inside_dollar_block:
    raise ValueError(
        "Unclosed $$ block found in SQL file."
    )

return statements
```

def execute_sql_files(conn, sql_files):
cursor = conn.cursor()

```
try:

    for sql_file in sql_files:

        print()
        print(f"Deploying: {sql_file}")

        with open(
            sql_file,
            "r",
            encoding="utf-8",
        ) as file:
            sql = file.read()

        statements = split_sql_statements(sql)

        print(
            f"Found {len(statements)} statement(s)"
        )

        for number, statement in enumerate(
            statements,
            start=1,
        ):

            print(
                f"  Executing statement "
                f"{number}/{len(statements)}..."
            )

            cursor.execute(statement)

        conn.commit()

        print(
            f"SUCCESS: {sql_file}"
        )

except Exception as e:

    print()
    print(
        f"ERROR while deploying {sql_file}:"
    )
    print(e)

    try:
        conn.rollback()
    except Exception:
        pass

    sys.exit(1)

finally:
    cursor.close()
```

def main():

```
print()
print("========================================")
print("SNOWFLAKE AGENT DEPLOYMENT")
print("========================================")

if is_ci_environment():
    print("Environment: GitHub Actions")
else:
    print("Environment: Local")

sql_files = get_sql_files()

print()
print("SQL files:")

for sql_file in sql_files:
    print(f"  - {sql_file}")

config = load_config()

print()
print(f"Database: {config['database']}")
print(f"Warehouse: {config['warehouse']}")

conn = connect_snowflake(config)

try:
    execute_sql_files(
        conn,
        sql_files,
    )
finally:
    conn.close()

print()
print("========================================")
print("DEPLOYMENT COMPLETED SUCCESSFULLY")
print("========================================")
```

if **name** == "**main**":
main()
