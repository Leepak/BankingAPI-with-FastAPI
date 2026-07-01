from fastapi import FastAPI
from fastapi.security import HTTPBearer, OAuth2PasswordBearer
from sqlalchemy import text

from app.database import engine, Base
from app.routes import customer, report, transaction,auth_route, account, user_route
from app.routes.user_route import router as user_router


app = FastAPI(
    title="Banking API",
    description="A comprehensive banking API with authentication, transaction, and reporting features",
    version="1.0.0"
)

# Create tables on startup
Base.metadata.create_all(bind=engine)

# Include router
app.include_router(auth_route.router)
app.include_router(user_route.router)
app.include_router(customer.router)

app.include_router(account.router)
app.include_router(transaction.router)
app.include_router(report.router)  # Include the report router



@app.get("/")
def root():
    return {"message": "Banking API is running successfully!"}


@app.get("/db-test")
def db_test():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return {
                "status": "success",
                "result": result.scalar()
            }
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }

    