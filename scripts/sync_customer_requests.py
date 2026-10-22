import sys
from sqlalchemy import text
from app.database import engine

def create_trigger_and_backfill():
    with engine.begin() as conn:
        print("Creating or replacing function customer_hj.sync_customer_request_to_sales()...")
        conn.execute(text("""
            CREATE OR REPLACE FUNCTION customer_hj.sync_customer_request_to_sales()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $$
            DECLARE
                v_name text;
                v_email text;
                v_phone text;
                v_country text;
                v_cust_details jsonb;
            BEGIN
                -- Determine customer details
                IF NEW.customer_details IS NOT NULL AND NEW.customer_details != '{}'::jsonb THEN
                    v_cust_details := NEW.customer_details;
                ELSE
                    -- Lookup customer from CUSTOMER_PROFILE if available
                    SELECT name, email, phone_number, country
                    INTO v_name, v_email, v_phone, v_country
                    FROM customer_hj."CUSTOMER_PROFILE"
                    WHERE customer_id = NEW.customer_id;

                    v_cust_details := jsonb_build_object(
                        'name', COALESCE(NEW.full_name, v_name, ''),
                        'email', COALESCE(NEW.email, v_email, ''),
                        'mobile', COALESCE(NEW.mobile_number, v_phone, ''),
                        'country', COALESCE(NEW.country, v_country, '')
                    );
                END IF;

                INSERT INTO sales_hj."SALES_REQUESTS_HJ" (
                    id,
                    request_number,
                    customer_id,
                    service_type,
                    service_sub_type,
                    people_count,
                    buget,
                    currency,
                    departure,
                    destination,
                    start_date,
                    end_date,
                    trip_type,
                    additional_requirements,
                    customer_details,
                    service_details,
                    request_mode,
                    created_at,
                    updated_at
                )
                VALUES (
                    NEW.id,
                    NEW.request_number::text,
                    NEW.customer_id::text,
                    NEW.service_type,
                    NEW.service_sub_type,
                    COALESCE(NEW.passenger_count, 1),
                    NEW.budget,
                    COALESCE(NEW.currency, 'USD'),
                    NEW.departure,
                    NEW.destination,
                    NEW.start_date,
                    NEW.end_date,
                    NEW.trip_type,
                    NEW.additional_requirements,
                    v_cust_details,
                    COALESCE(NEW.service_details, '{}'::jsonb),
                    COALESCE(NEW.category, 'ONLINE'),
                    COALESCE(NEW.created_at, CURRENT_TIMESTAMP),
                    COALESCE(NEW.updated_at, CURRENT_TIMESTAMP)
                )
                ON CONFLICT (id) DO UPDATE SET
                    request_number = EXCLUDED.request_number,
                    customer_id = EXCLUDED.customer_id,
                    service_type = EXCLUDED.service_type,
                    service_sub_type = EXCLUDED.service_sub_type,
                    people_count = EXCLUDED.people_count,
                    buget = EXCLUDED.buget,
                    currency = EXCLUDED.currency,
                    departure = EXCLUDED.departure,
                    destination = EXCLUDED.destination,
                    start_date = EXCLUDED.start_date,
                    end_date = EXCLUDED.end_date,
                    trip_type = EXCLUDED.trip_type,
                    additional_requirements = EXCLUDED.additional_requirements,
                    customer_details = EXCLUDED.customer_details,
                    service_details = EXCLUDED.service_details,
                    request_mode = EXCLUDED.request_mode,
                    updated_at = EXCLUDED.updated_at;

                RETURN NEW;
            END;
            $$;
        """))
        print("Function created.")

        print("Attaching trigger trg_sync_customer_request to customer_hj.\"CUSTOMER_REQUESTS\"...")
        conn.execute(text("""
            DROP TRIGGER IF EXISTS trg_sync_customer_request ON customer_hj."CUSTOMER_REQUESTS";
            CREATE TRIGGER trg_sync_customer_request
            AFTER INSERT OR UPDATE ON customer_hj."CUSTOMER_REQUESTS"
            FOR EACH ROW
            EXECUTE FUNCTION customer_hj.sync_customer_request_to_sales();
        """))
        print("Trigger attached.")

        print("Backfilling existing records from customer_hj.\"CUSTOMER_REQUESTS\" to sales_hj.\"SALES_REQUESTS_HJ\"...")
        conn.execute(text("""
            INSERT INTO sales_hj."SALES_REQUESTS_HJ" (
                id,
                request_number,
                customer_id,
                service_type,
                service_sub_type,
                people_count,
                buget,
                currency,
                departure,
                destination,
                start_date,
                end_date,
                trip_type,
                additional_requirements,
                customer_details,
                service_details,
                request_mode,
                created_at,
                updated_at
            )
            SELECT 
                r.id,
                r.request_number::text,
                r.customer_id::text,
                r.service_type,
                r.service_sub_type,
                COALESCE(r.passenger_count, 1),
                r.budget,
                COALESCE(r.currency, 'USD'),
                r.departure,
                r.destination,
                r.start_date,
                r.end_date,
                r.trip_type,
                r.additional_requirements,
                CASE 
                    WHEN r.customer_details IS NOT NULL AND r.customer_details != '{}'::jsonb THEN r.customer_details
                    ELSE jsonb_build_object(
                        'name', COALESCE(r.full_name, p.name, ''),
                        'email', COALESCE(r.email, p.email, ''),
                        'mobile', COALESCE(r.mobile_number, p.phone_number, ''),
                        'country', COALESCE(r.country, p.country, '')
                    )
                END,
                COALESCE(r.service_details, '{}'::jsonb),
                COALESCE(r.category, 'ONLINE'),
                COALESCE(r.created_at, CURRENT_TIMESTAMP),
                COALESCE(r.updated_at, CURRENT_TIMESTAMP)
            FROM customer_hj."CUSTOMER_REQUESTS" r
            LEFT JOIN customer_hj."CUSTOMER_PROFILE" p ON r.customer_id = p.customer_id
            ON CONFLICT (id) DO UPDATE SET
                request_number = EXCLUDED.request_number,
                customer_id = EXCLUDED.customer_id,
                service_type = EXCLUDED.service_type,
                service_sub_type = EXCLUDED.service_sub_type,
                people_count = EXCLUDED.people_count,
                buget = EXCLUDED.buget,
                currency = EXCLUDED.currency,
                departure = EXCLUDED.departure,
                destination = EXCLUDED.destination,
                start_date = EXCLUDED.start_date,
                end_date = EXCLUDED.end_date,
                trip_type = EXCLUDED.trip_type,
                additional_requirements = EXCLUDED.additional_requirements,
                customer_details = EXCLUDED.customer_details,
                service_details = EXCLUDED.service_details,
                request_mode = EXCLUDED.request_mode,
                updated_at = EXCLUDED.updated_at;
        """))
        print("Backfill completed successfully.")

if __name__ == "__main__":
    create_trigger_and_backfill()
