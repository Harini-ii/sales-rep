from fastapi import FastAPI
from app.routers import customers, requests, tickets, profile, images

app = FastAPI(
    title="Helite Jet Sales Dashboard API",
    description="API for managing customers, aviation requests, support tickets, and images.",
    version="1.0.0"
)

app.include_router(customers.router)
app.include_router(requests.router)
app.include_router(tickets.router)
app.include_router(profile.router)
app.include_router(images.router)

@app.get("/")
def home():
    return {"message": "Sales are Working"}

def custom_openapi():
    from fastapi.openapi.utils import get_openapi
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Remove required array from all components/schemas (Request Bodies)
    if "components" in openapi_schema and "schemas" in openapi_schema["components"]:
        for schema_name, schema_data in openapi_schema["components"]["schemas"].items():
            if "required" in schema_data:
                del schema_data["required"]
                
    # Remove required flags from all path and query parameters, and request bodies in paths
    if "paths" in openapi_schema:
        for path, path_data in openapi_schema["paths"].items():
            for method, method_data in path_data.items():
                if "parameters" in method_data:
                    for param in method_data["parameters"]:
                        param["required"] = False
                if "requestBody" in method_data and "required" in method_data["requestBody"]:
                    method_data["requestBody"]["required"] = False

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
