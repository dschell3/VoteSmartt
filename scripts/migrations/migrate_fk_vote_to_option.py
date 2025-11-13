"""
Migration: fix `vote.vote_option_id` foreign key to reference `option`(option_id).
Idempotent: only drops/adds when necessary.

Usage:
  python scripts/migrations/migrate_fk_vote_to_option.py
"""
"""# Maintenance note: Prevents FK mismatch errors; could be merged into a versioned migration tool; safe to remove after all DBs upgraded."""
from flask_app.config.mysqlconnection import connectToMySQL

DB = "mydb"


def get_vote_fk_target():
    rows = connectToMySQL(DB).query_db(
        """
        SELECT kcu.constraint_name, kcu.referenced_table_name
        FROM information_schema.key_column_usage kcu
        WHERE kcu.table_schema=%(schema)s
          AND kcu.table_name='vote'
          AND kcu.column_name='vote_option_id'
          AND kcu.referenced_table_name IS NOT NULL;
        """,
        {"schema": DB},
    ) or []
    return rows


def drop_fk_if_exists(name: str):
    # Check existence by name
    rows = connectToMySQL(DB).query_db(
        """
        SELECT constraint_name FROM information_schema.table_constraints
        WHERE table_schema=%(schema)s AND table_name='vote' AND constraint_name=%(name)s;
        """,
        {"schema": DB, "name": name},
    ) or []
    if rows:
        return connectToMySQL(DB).query_db("ALTER TABLE vote DROP FOREIGN KEY %s;" % name)
    return True


def add_fk_if_missing(name: str):
    # If any FK on vote_option_id already points to `option`, skip
    rows = get_vote_fk_target()
    if any(r.get("REFERENCED_TABLE_NAME") == "option" for r in rows):
        return True
    return connectToMySQL(DB).query_db(
        """
        ALTER TABLE vote
        ADD CONSTRAINT %s
        FOREIGN KEY (vote_option_id)
        REFERENCES `option` (option_id)
        ON DELETE CASCADE;
        """ % name
    )


def main():
    before = get_vote_fk_target()
    print("Before:", before)

    # If FK points to `choices`, drop and recreate; if missing, just add; if already correct then skip
    need_drop = any(r.get("REFERENCED_TABLE_NAME") == "choices" for r in before)
    if need_drop:
        print("Dropping old FK fk_vote_option1 ...")
        drop_fk_if_exists("fk_vote_option1")
    else:
        print("No need to drop existing FK by name.")

    print("Ensuring FK -> `option` ...")
    add_fk_if_missing("fk_vote_option1")

    after = get_vote_fk_target()
    print("After:", after)


if __name__ == "__main__":
    main()
