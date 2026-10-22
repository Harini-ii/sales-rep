from datetime import date

# In-memory dictionary to act as our "database"
customers_db = {
    1: {
        "id": 1,
        "name": "John Doe",
        "email": "john.doe@example.com",
        "mobile": "+1234567890",
        "subscription": "Premium",
        "credits": 500,
        "purchases": 12,
        "country": "USA",
        "company": "Helite Corp",
        "joined": date(2023, 1, 15)
    },
    2: {
        "id": 2,
        "name": "Jane Smith",
        "email": "jane.smith@example.com",
        "mobile": "+0987654321",
        "subscription": "Basic",
        "credits": 100,
        "purchases": 3,
        "country": "UK",
        "company": "Jet Solutions",
        "joined": date(2023, 5, 20)
    }
}

requests_db = {
    "HJ-01016": {
        "request_id": "HJ-01016",
        "customer_id": "404f0418-5ac5-4f86-b38a-f69930ba9c13",
        "email": "Not provided",
        "mobile": "Not provided",
        "status": "BOOKED",
        "service": "AVIATION",
        "passengers": 1,
        "event_flight_details": {
            "event_type": "Not provided",
            "timing": "Not provided",
            "date": "Not provided",
            "time": "Not provided",
            "aircraft": "Not provided",
            "aircraft_type": "Not provided",
            "capacity": "Not provided",
            "food": "Not provided",
            "drinks": "Not provided",
            "champagne": "Not requested",
            "crew_preferences": "Not provided"
        },
        "customer_details": {
            "name": "Not provided",
            "email": "Not provided"
        }
    }
}

tickets_db = []
ticket_counter = 1

# Mock Profile Data
profile_db = {
    "full_name": "Gowtham",
    "email": "gowtham@gmail.com",
    "mobile": "1234567890",
    "password": "oldpassword"  # Storing plain text just for mock purposes
}

# Temporary In-Memory Storage for Images (resets on server restart)
# Prepared for future replacement when team lead provides actual database.
images_db = []
image_counter = 1

def get_all_images():
    """Retrieve all temporary in-memory image records."""
    return list(images_db)

def get_image_by_id(image_id: str):
    """Retrieve an image record by its unique identifier."""
    for img in images_db:
        if img["image_id"] == image_id:
            return img
    return None

def find_duplicate_image(image_name: str, image_url: str):
    """
    Check if an image with the same name or URL already exists.
    Returns a tuple (is_duplicate: bool, reason: str).
    """
    normalized_name = image_name.strip().lower()
    normalized_url = image_url.strip()
    for img in images_db:
        if img["image_name"].strip().lower() == normalized_name:
            return True, f"An image with name '{image_name}' already exists in temporary storage."
        if img["image_url"].strip() == normalized_url:
            return True, f"An image with URL '{image_url}' already exists in temporary storage."
    return False, ""

def create_image_record(image_name: str, image_url: str, created_at):
    """
    Create a new image record in temporary in-memory storage.
    """
    global image_counter
    image_id = f"IMG-{image_counter:03d}"
    image_counter += 1
    record = {
        "image_id": image_id,
        "image_name": image_name.strip(),
        "image_url": str(image_url),
        "created_at": created_at,
        "storage_type": "in_memory_temporary",
        "is_persisted_to_db": False,
        "note": "Temporary in-memory record; resets on server restart. Database persistence pending."
    }
    images_db.append(record)
    return record

def delete_image_by_id(image_id: str):
    """Delete an image record by ID from temporary storage (useful for testing)."""
    for index, img in enumerate(images_db):
        if img["image_id"] == image_id:
            return images_db.pop(index)
    return None

def reset_images():
    """Reset temporary in-memory images store."""
    global image_counter
    images_db.clear()
    image_counter = 1

