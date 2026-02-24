from datetime import datetime
from fastapi import FastAPI
from database import SessionLocal, engine
from models import License, Base

app = FastAPI()

# 🔥 tables create here
Base.metadata.create_all(bind=engine)

@app.post("/verify")
def verify_license(key: str):
    db = SessionLocal()
    try:
        license = db.query(License).filter(License.key == key).first()

        if not license:
            return {"status": "invalid"}

        if license.status != "active":
            return {"status": license.status}

        if not license.expiry:
            return {"status": "error", "message": "expiry not set"}

        if datetime.utcnow() > license.expiry:
            license.status = "expired"
            db.commit()
            return {"status": "expired"}

        return {
            "status": "valid",
            "expiry": str(license.expiry),
            "device_limit": license.device_limit,
            "device_used": license.device_used
        }

    except Exception as e:
        return {"error": str(e)}

    finally:
        db.close()
