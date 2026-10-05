# Snowflake Agent Deployment Script

import os
import glob
import sys
import snowflake.connector

def split_sql_statements(sql):
    statements = []
    current = []

    inside_dollar_block = False
    inside_line_comment = False
    inside_block_comment = False

    i = 0

    while i < len(sql):

        # ------------------------------------------------------------
        # LINE COMMENT
        # ------------------------------------------------------------
        if inside_line_comment:

            if sql[i] == "\n":
                inside_line_comment = False
                current.append("\n")

            i += 1
            continue

        # ------------------------------------------------------------
        # BLOCK COMMENT
        # ------------------------------------------------------------
        if inside_block_comment:

            if sql[i:i + 2] == "*/":
                inside_block_comment = False
                i += 2
            else:
                i += 1

            continue

        # ------------------------------------------------------------
        # START LINE COMMENT
        # ------------------------------------------------------------
        if not inside_dollar_block and sql[i:i + 2] == "--":
            inside_line_comment = True
            i += 2
            continue

        # ------------------------------------------------------------
        # START BLOCK COMMENT
        # ------------------------------------------------------------
        if not inside_dollar_block and sql[i:i + 2] == "/*":
            inside_block_comment = True
            i += 2
            continue

        # ------------------------------------------------------------
        # START / END $$ BLOCK
        # ------------------------------------------------------------
        if sql[i:i + 2] == "$$":

            current.append("$$")

            inside_dollar_block = not inside_dollar_block

            i += 2
            continue

        # ------------------------------------------------------------
        # STATEMENT TERMINATOR
        # ------------------------------------------------------------
        if sql[i] == ";" and not inside_dollar_block:

            statement = "".join(current).strip()

            if statement:
                statements.append(statement)

            current = []

            i += 1
            continue

        # ------------------------------------------------------------
        # NORMAL CHARACTER
        # ------------------------------------------------------------
        current.append(sql[i])

        i += 1

    # ------------------------------------------------------------
    # FINAL STATEMENT
    # ------------------------------------------------------------

    statement = "".join(current).strip()

    if statement:
        statements.append(statement)

    # ------------------------------------------------------------
    # VALIDATION
    # ------------------------------------------------------------

    if inside_dollar_block:
        raise Exception("Unclosed $$ block in SQL file")

    if inside_block_comment:
        raise Exception("Unclosed /* */ comment in SQL file")

    return statements


def main():

    print("========================================")
    print("SNOWFLAKE DEPLOYMENT")
    print("========================================")

    account = os.environ.get("SNOWFLAKE_ACCOUNT")
    user = os.environ.get("SNOWFLAKE_USER")
    password = os.environ.get("SNOWFLAKE_PASSWORD")
    database = os.environ.get("SNOWFLAKE_DATABASE")
    warehouse = os.environ.get("SNOWFLAKE_WAREHOUSE")

    if not account:
        print("ERROR: SNOWFLAKE_ACCOUNT is missing")
        sys.exit(1)

    if not user:
        print("ERROR: SNOWFLAKE_USER is missing")
        sys.exit(1)

    if not password:
        print("ERROR: SNOWFLAKE_PASSWORD is missing")
        sys.exit(1)

    if not database:
        print("ERROR: SNOWFLAKE_DATABASE is missing")
        sys.exit(1)

    if not warehouse:
        print("ERROR: SNOWFLAKE_WAREHOUSE is missing")
        sys.exit(1)

    sql_files = sorted(glob.glob("sql/*.sql"))

    if not sql_files:
        print("ERROR: No SQL files found")
        sys.exit(1)

    print("Database:", database)
    print("Warehouse:", warehouse)
    print()
    print("SQL files:")

    for sql_file in sql_files:
        print(" -", sql_file)

    print()
    print("Connecting to Snowflake...")

    try:

        conn = snowflake.connector.connect(
            account=account,
            user=user,
            password=password,
            database=database,
            warehouse=warehouse
        )

        print("Connected successfully")
        print()

    except Exception as e:

        print("ERROR: Snowflake connection failed")
        print(e)
        sys.exit(1)

    cursor = conn.cursor()

    try:

        for sql_file in sql_files:

            print("----------------------------------------")
            print("Deploying:", sql_file)
            print("----------------------------------------")

            with open(
                sql_file,
                "r",
                encoding="utf-8"
            ) as file:

                sql = file.read()

            statements = split_sql_statements(sql)

            print(
                "Found",
                len(statements),
                "statement(s)"
            )

            for number, statement in enumerate(
                statements,
                1
            ):

                print(
                    "Executing statement",
                    number,
                    "of",
                    len(statements)
                )

                cursor.execute(statement)

            conn.commit()

            print("SUCCESS:", sql_file)
            print()

    except Exception as e:

        print()
        print("ERROR during deployment:")
        print(e)

        try:
            conn.rollback()
        except Exception:
            pass

        sys.exit(1)

    finally:

        cursor.close()
        conn.close()

    print("========================================")
    print("DEPLOYMENT COMPLETED SUCCESSFULLY")
    print("========================================")


if __name__ == "__main__":
    main()