from flask_app.config.mysqlconnection import connectToMySQL  # Maintenance note: Legacy one-off FK fix; prefer idempotent version in scripts/migrations; safe to remove later.

DB = "mydb"

def main():
    # Verify current FK
    fk_before = connectToMySQL(DB).query_db(
        """
        SELECT kcu.constraint_name, kcu.referenced_table_name
        FROM information_schema.key_column_usage kcu
        WHERE kcu.table_schema=%(schema)s AND kcu.table_name='vote' AND kcu.column_name='vote_option_id' AND kcu.referenced_table_name IS NOT NULL;
        """,
        {"schema": DB}
    )
    print("Before:", fk_before)

    # Drop FK if exists
    dropped = connectToMySQL(DB).query_db("ALTER TABLE vote DROP FOREIGN KEY fk_vote_option1;")
    print("Drop fk_vote_option1:", dropped)

    # Add FK to `option`
    added = connectToMySQL(DB).query_db(
        """
        ALTER TABLE vote
        ADD CONSTRAINT fk_vote_option1
        FOREIGN KEY (vote_option_id)
        REFERENCES `option` (option_id)
        ON DELETE CASCADE;
        """
    )
    print("Add fk_vote_option1 -> `option`:", added)

    # Verify after
    fk_after = connectToMySQL(DB).query_db(
        """
        SELECT kcu.constraint_name, kcu.referenced_table_name
        FROM information_schema.key_column_usage kcu
        WHERE kcu.table_schema=%(schema)s AND kcu.table_name='vote' AND kcu.column_name='vote_option_id' AND kcu.referenced_table_name IS NOT NULL;
        """,
        {"schema": DB}
    )
    print("After:", fk_after)

if __name__ == "__main__":
    main()
