import sys
from sqlalchemy import text
from app.database import engine

def convert_all_ids_to_uuid():
    with engine.begin() as conn:
        print("1. Converting CUSTOMERS_HJ id to UUID...")
        conn.execute(text('ALTER TABLE sales_hj."CUSTOMERS_HJ" ALTER COLUMN id DROP DEFAULT;'))
        conn.execute(text('ALTER TABLE sales_hj."CUSTOMERS_HJ" ALTER COLUMN id TYPE uuid USING customer_id;'))
        conn.execute(text('ALTER TABLE sales_hj."CUSTOMERS_HJ" ALTER COLUMN id SET DEFAULT gen_random_uuid();'))
        print("   -> CUSTOMERS_HJ id is now UUID matching customer_id.")

        print("2. Converting AIRCRAFT_IMAGES_HJ image_id to native UUID...")
        conn.execute(text('ALTER TABLE sales_hj."AIRCRAFT_IMAGES_HJ" ALTER COLUMN image_id TYPE uuid USING image_id::uuid;'))
        print("   -> AIRCRAFT_IMAGES_HJ image_id is now native UUID.")

        print("3. Converting SALES_REQUESTS_HJ customer_id to native UUID...")
        conn.execute(text('ALTER TABLE sales_hj."SALES_REQUESTS_HJ" ALTER COLUMN customer_id TYPE uuid USING customer_id::uuid;'))
        print("   -> SALES_REQUESTS_HJ customer_id is now native UUID.")

        print("4. Converting REQUEST_STATUS_HISTORY_HJ id to UUID...")
        conn.execute(text('ALTER TABLE sales_hj."REQUEST_STATUS_HISTORY_HJ" DROP CONSTRAINT IF EXISTS request_status_history_pkey;'))
        conn.execute(text('ALTER TABLE sales_hj."REQUEST_STATUS_HISTORY_HJ" ALTER COLUMN id DROP DEFAULT;'))
        conn.execute(text('ALTER TABLE sales_hj."REQUEST_STATUS_HISTORY_HJ" ALTER COLUMN id TYPE uuid USING gen_random_uuid();'))
        conn.execute(text('ALTER TABLE sales_hj."REQUEST_STATUS_HISTORY_HJ" ALTER COLUMN id SET DEFAULT gen_random_uuid();'))
        conn.execute(text('ALTER TABLE sales_hj."REQUEST_STATUS_HISTORY_HJ" ADD PRIMARY KEY (id);'))
        print("   -> REQUEST_STATUS_HISTORY_HJ id is now UUID.")

        print("5. Converting PASSWORD_CHANGES_HJ id to UUID...")
        conn.execute(text('ALTER TABLE sales_hj."PASSWORD_CHANGES_HJ" DROP CONSTRAINT IF EXISTS password_changes_pkey;'))
        conn.execute(text('ALTER TABLE sales_hj."PASSWORD_CHANGES_HJ" ALTER COLUMN id DROP DEFAULT;'))
        conn.execute(text('ALTER TABLE sales_hj."PASSWORD_CHANGES_HJ" ALTER COLUMN id TYPE uuid USING gen_random_uuid();'))
        conn.execute(text('ALTER TABLE sales_hj."PASSWORD_CHANGES_HJ" ALTER COLUMN id SET DEFAULT gen_random_uuid();'))
        conn.execute(text('ALTER TABLE sales_hj."PASSWORD_CHANGES_HJ" ADD PRIMARY KEY (id);'))
        print("   -> PASSWORD_CHANGES_HJ id is now UUID.")

        print("6. Converting PERSONAL_INFORMATION_HJ id to UUID...")
        conn.execute(text('ALTER TABLE sales_hj."PERSONAL_INFORMATION_HJ" DROP CONSTRAINT IF EXISTS personal_information_pkey;'))
        conn.execute(text('ALTER TABLE sales_hj."PERSONAL_INFORMATION_HJ" ALTER COLUMN id DROP DEFAULT;'))
        conn.execute(text('ALTER TABLE sales_hj."PERSONAL_INFORMATION_HJ" ALTER COLUMN id TYPE uuid USING gen_random_uuid();'))
        conn.execute(text('ALTER TABLE sales_hj."PERSONAL_INFORMATION_HJ" ALTER COLUMN id SET DEFAULT gen_random_uuid();'))
        conn.execute(text('ALTER TABLE sales_hj."PERSONAL_INFORMATION_HJ" ADD PRIMARY KEY (id);'))
        print("   -> PERSONAL_INFORMATION_HJ id is now UUID.")

        print("7. Updating trigger function customer_hj.sync_customer_to_sales()...")
        conn.execute(text("""
            CREATE OR REPLACE FUNCTION customer_hj.sync_customer_to_sales()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $function$
            BEGIN
                INSERT INTO sales_hj."CUSTOMERS_HJ" (
                    id, customer_id, name, email, mobile, country, company, joined, created_at, subscription, credits, purchases
                )
                VALUES (
                    NEW.customer_id,
                    NEW.customer_id,
                    NEW.name,
                    NEW.email,
                    COALESCE(NEW.phone_number, ''),
                    COALESCE(NEW.country, ''),
                    COALESCE(NEW.company, ''),
                    NEW.created_at::date,
                    NEW.created_at,
                    'Basic',
                    0,
                    0
                )
                ON CONFLICT (customer_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    email = EXCLUDED.email,
                    mobile = EXCLUDED.mobile,
                    country = EXCLUDED.country,
                    company = EXCLUDED.company;
                RETURN NEW;
            END;
            $function$;
        """))
        print("   -> Trigger function updated.")

    print("\nALL ID COLUMNS CONVERTED TO UUID FORMAT SUCCESSFULLY!")

if __name__ == "__main__":
    convert_all_ids_to_uuid()
