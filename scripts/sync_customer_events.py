import sys
from sqlalchemy import text
from app.database import engine

def sync_events():
    with engine.begin() as conn:
        print("Fetching all column names from customer_hj.CUSTOMER_EVENTS...")
        cols = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'customer_hj' AND table_name = 'CUSTOMER_EVENTS'
            ORDER BY ordinal_position;
        """)).scalars().all()
        
        print(f"Found {len(cols)} columns.")
        
        # 1. Update column types in sales_hj.SALES_EVENTS_HJ to match UUIDs
        print("Aligning event_id and customer_id to UUID in sales_hj.SALES_EVENTS_HJ...")
        conn.execute(text('ALTER TABLE sales_hj."SALES_EVENTS_HJ" DROP CONSTRAINT IF EXISTS sales_events_hj_pkey;'))
        conn.execute(text('ALTER TABLE sales_hj."SALES_EVENTS_HJ" ALTER COLUMN event_id DROP DEFAULT;'))
        conn.execute(text('ALTER TABLE sales_hj."SALES_EVENTS_HJ" ALTER COLUMN event_id TYPE uuid USING gen_random_uuid();'))
        conn.execute(text('ALTER TABLE sales_hj."SALES_EVENTS_HJ" ALTER COLUMN customer_id TYPE uuid USING NULL;'))
        conn.execute(text('ALTER TABLE sales_hj."SALES_EVENTS_HJ" ADD PRIMARY KEY (event_id);'))
        print("Column types aligned and Primary Key set.")

        # 2. Build trigger function SQL
        cols_str = ", ".join([f'"{c}"' for c in cols])
        vals_str = ", ".join([f'NEW."{c}"' for c in cols])
        update_assignments = ", ".join([f'"{c}" = EXCLUDED."{c}"' for c in cols if c != "event_id"])

        func_sql = f"""
        CREATE OR REPLACE FUNCTION customer_hj.sync_customer_event_to_sales()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            INSERT INTO sales_hj."SALES_EVENTS_HJ" (
                {cols_str}
            )
            VALUES (
                {vals_str}
            )
            ON CONFLICT (event_id) DO UPDATE SET
                {update_assignments};
            RETURN NEW;
        END;
        $$;
        """

        print("Creating or replacing function customer_hj.sync_customer_event_to_sales()...")
        conn.execute(text(func_sql))
        print("Function created.")

        # 3. Create Trigger on customer_hj.CUSTOMER_EVENTS
        print("Attaching trigger trg_sync_customer_event to customer_hj.CUSTOMER_EVENTS...")
        conn.execute(text("""
            DROP TRIGGER IF EXISTS trg_sync_customer_event ON customer_hj."CUSTOMER_EVENTS";
            CREATE TRIGGER trg_sync_customer_event
            AFTER INSERT OR UPDATE ON customer_hj."CUSTOMER_EVENTS"
            FOR EACH ROW
            EXECUTE FUNCTION customer_hj.sync_customer_event_to_sales();
        """))
        print("Trigger attached.")

        # 4. Backfill existing records
        print("Backfilling existing records from customer_hj.CUSTOMER_EVENTS to sales_hj.SALES_EVENTS_HJ...")
        conn.execute(text('TRUNCATE sales_hj."SALES_EVENTS_HJ";'))
        backfill_sql = f"""
            INSERT INTO sales_hj."SALES_EVENTS_HJ" ({cols_str})
            SELECT {cols_str} FROM customer_hj."CUSTOMER_EVENTS";
        """
        res = conn.execute(text(backfill_sql))
        print(f"Backfilled {res.rowcount} records successfully.")

if __name__ == "__main__":
    sync_events()
