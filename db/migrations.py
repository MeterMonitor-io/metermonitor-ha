import sqlite3
import json
from datetime import datetime

def run_migrations(db_file):
    with sqlite3.connect(db_file) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # For <= 1.2.3: Add outdated bool to evaluations table if it doesn't exist yet
        cursor.execute("PRAGMA table_info(evaluations)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'outdated' not in columns:
            cursor.execute('''
                ALTER TABLE evaluations
                ADD COLUMN outdated BOOLEAN DEFAULT 0
            ''')
            print("[MIGRATION] Added 'outdated' column to 'evaluations' table")
            # re-read columns after altering
            cursor.execute("PRAGMA table_info(evaluations)")
            columns = [info[1] for info in cursor.fetchall()]

        # Migrate from old schema (name, eval JSON string) to new explicit columns
        # Only run if the legacy 'eval' column exists and new columns are not present yet
        new_cols_needed = {'colored_digits', 'th_digits', 'predictions', 'timestamp', 'result', 'total_confidence'}
        if 'eval' in columns and not new_cols_needed.intersection(set(columns)):
            print("[MIGRATION] Starting evaluations table migration (eval JSON -> explicit columns)")

            # Create new table with desired schema (assumes original table had only 'name' and 'eval')
            cursor.execute('''
                CREATE TABLE evaluations_new (
                    name TEXT,
                    colored_digits TEXT,
                    th_digits TEXT,
                    predictions TEXT,
                    timestamp DATETIME,
                    result INTEGER,
                    total_confidence REAL,
                    outdated BOOLEAN DEFAULT 0
                )
            ''')

            # Copy and transform rows
            cursor.execute("SELECT name, eval, outdated FROM evaluations")
            rows = cursor.fetchall()
            for row in rows:
                name = row["name"]
                eval_str = row["eval"]
                outdated_val = row["outdated"] if "outdated" in row.keys() else 0

                # Default values
                colored_json = None
                th_json = None
                predictions_json = None
                timestamp_val = None
                result_val = None
                total_conf_val = None

                # Parse eval JSON safely
                try:
                    parsed = json.loads(eval_str) if eval_str else []
                except Exception:
                    parsed = []

                # Map indices to new columns
                if isinstance(parsed, list):
                    if len(parsed) > 0 and parsed[0] is not None:
                        # store as JSON string (array of base64 strings)
                        try:
                            colored_json = json.dumps(parsed[0])
                        except Exception:
                            colored_json = None
                    if len(parsed) > 1 and parsed[1] is not None:
                        try:
                            th_json = json.dumps(parsed[1])
                        except Exception:
                            th_json = None
                    if len(parsed) > 2 and parsed[2] is not None:
                        try:
                            predictions_json = json.dumps(parsed[2])
                        except Exception:
                            predictions_json = None
                    if len(parsed) > 3 and parsed[3]:
                        # Try to parse ISO timestamp; store as ISO string if valid
                        try:
                            dt = datetime.fromisoformat(parsed[3])
                            timestamp_val = dt.isoformat(sep='T')
                        except Exception:
                            # If parsing fails, attempt to store raw string; if empty, keep None
                            timestamp_val = parsed[3] if isinstance(parsed[3], str) and parsed[3].strip() else None
                    if len(parsed) > 4:
                        # result may be null
                        result_val = parsed[4] if parsed[4] is not None else None
                    if len(parsed) > 6:
                        try:
                            total_conf_val = float(parsed[6]) if parsed[6] is not None else None
                        except Exception:
                            total_conf_val = None

                cursor.execute('''
                    INSERT INTO evaluations_new
                    (name, colored_digits, th_digits, predictions, timestamp, result, total_confidence, outdated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (name, colored_json, th_json, predictions_json, timestamp_val, result_val, total_conf_val, outdated_val))

            # Replace old table
            cursor.execute("DROP TABLE evaluations")
            cursor.execute("ALTER TABLE evaluations_new RENAME TO evaluations")
            conn.commit()
            print("[MIGRATION] Completed evaluations table migration")

        # Add auto-incrementing ID primary key to evaluations table
        cursor.execute("PRAGMA table_info(evaluations)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'id' not in columns:
            print("[MIGRATION] Adding auto-incrementing ID primary key to evaluations table")

            # Create new table with id as primary key
            cursor.execute('''
                CREATE TABLE evaluations_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    colored_digits TEXT,
                    th_digits TEXT,
                    predictions TEXT,
                    timestamp DATETIME,
                    result INTEGER,
                    total_confidence REAL,
                    outdated BOOLEAN DEFAULT 0,
                    FOREIGN KEY(name) REFERENCES watermeters(name)
                )
            ''')

            # Copy all data from old table
            cursor.execute('''
                INSERT INTO evaluations_new 
                (name, colored_digits, th_digits, predictions, timestamp, result, total_confidence, outdated)
                SELECT name, colored_digits, th_digits, predictions, timestamp, result, total_confidence, outdated
                FROM evaluations
            ''')

            # Replace old table
            cursor.execute("DROP TABLE evaluations")
            cursor.execute("ALTER TABLE evaluations_new RENAME TO evaluations")
            conn.commit()
            print("[MIGRATION] Added ID primary key to evaluations table")
        # Add auto-incrementing ID primary key to history table
        cursor.execute("PRAGMA table_info(history)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'id' not in columns:
            print("[MIGRATION] Adding auto-incrementing ID primary key to history table")

            # Create new table with id as primary key
            cursor.execute('''
                CREATE TABLE history_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    value INTEGER,
                    confidence REAL,
                    target_brightness REAL,
                    timestamp TEXT,
                    manual BOOLEAN,
                    FOREIGN KEY(name) REFERENCES watermeters(name)
                )
            ''')

            # Copy all data from old table
            cursor.execute('''
                INSERT INTO history_new 
                (name, value, confidence, target_brightness, timestamp, manual)
                SELECT name, value, confidence, target_brightness, timestamp, manual
                FROM history
            ''')

            # Replace old table
            cursor.execute("DROP TABLE history")
            cursor.execute("ALTER TABLE history_new RENAME TO history")
            conn.commit()
            print("[MIGRATION] Added ID primary key to history table")

        # add column picture_data_bbox to watermeters table if it doesn't exist yet
        cursor.execute("PRAGMA table_info(watermeters)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'picture_data_bbox' not in columns:
            cursor.execute('''
                ALTER TABLE watermeters
                ADD COLUMN picture_data_bbox BLOB
            ''')
            print("[MIGRATION] Added 'picture_data_bbox' column to 'watermeters' table")


