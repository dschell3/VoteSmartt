"""
Migration: ensure table `option` exists.
Safe to run multiple times.

Usage:
  python scripts/migrations/create_option_table.py
"""
# Maintenance note: Ensures schema is present to avoid runtime failures; could be folded into a formal migration system; delete once migrations are standardized.
from flask_app.config.mysqlconnection import connectToMySQL

DB = "mydb"

SQL = """
CREATE TABLE IF NOT EXISTS `option` (
  `option_id` INT NOT NULL AUTO_INCREMENT,
  `option_text` VARCHAR(255) NOT NULL,
  `option_event_id` INT NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`option_id`),
  KEY `idx_option_event_id` (`option_event_id`),
  CONSTRAINT `fk_option_event`
    FOREIGN KEY (`option_event_id`) REFERENCES `event`(`event_id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""


def main():
    res = connectToMySQL(DB).query_db(SQL)
    print('Option table ensured:', res)


if __name__ == '__main__':
    main()
