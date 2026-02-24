from fastapi import FastAPI
from database import SessionLocal
from models import License
from datetime import datetime

app = FastAPI()

def db():
    return SessionLocal()

@app.post("/verify")
def verify_license(key: str):
    session = db()
    license = session.query(License).filter_by(key=key).first()

    if not license:
        return {"status": "invalid"}

    if license.status != "active":
        return {"status": license.status}

    if datetime.utcnow() > license.expiry:
        license.status = "expired"
        session.commit()
        return {"status": "expired"}

    return {
        "status": "valid",
        "expiry": license.expiry
    }
