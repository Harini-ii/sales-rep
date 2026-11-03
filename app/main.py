from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from app.routers import customers, requests, tickets, profile, images, events, dashboard

app = FastAPI(
    title="Helite Jet Sales Dashboard API",
    description="API for managing customers, aviation requests, support tickets, images, and events.",
    version="1.0.0"
)

# Enable CORS for web and mobile frontends (pushpakavimanam & Flutter)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Standard endpoints
app.include_router(dashboard.router)
app.include_router(customers.router)
app.include_router(requests.router)
app.include_router(events.router)
app.include_router(tickets.router)
app.include_router(profile.router)
app.include_router(images.router)

# Support /sales prefix for frontend callers (pushpakavimanam)
app.include_router(customers.router, prefix="/sales")
app.include_router(requests.router, prefix="/sales")
app.include_router(events.router, prefix="/sales")
app.include_router(tickets.router, prefix="/sales")
app.include_router(profile.router, prefix="/sales")
app.include_router(images.router, prefix="/sales")

# Support /support and /sales/support aliases
support_alias = APIRouter(tags=["Support"])
support_alias.add_api_route("/", tickets.get_tickets, methods=["GET"], response_model=tickets.TicketListResponse)
support_alias.add_api_route("", tickets.get_tickets, methods=["GET"], response_model=tickets.TicketListResponse, include_in_schema=False)
support_alias.add_api_route("/", tickets.create_ticket, methods=["POST"], response_model=tickets.Ticket, status_code=201)
support_alias.add_api_route("", tickets.create_ticket, methods=["POST"], response_model=tickets.Ticket, status_code=201, include_in_schema=False)
support_alias.add_api_route("/{ticket_id}", tickets.get_ticket_by_id, methods=["GET"], response_model=tickets.Ticket)

app.include_router(support_alias, prefix="/support")
app.include_router(support_alias, prefix="/sales/support")

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
