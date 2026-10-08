import threading
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.session import Base
from app.models.case import ClinicalCase
from app.models.user import User
from app.routers.cases import claim_case_for_veterinarian

engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

db = Session()
for email in ['v1@example.com', 'v2@example.com']:
    user = User(full_name='Demo', email=email, password_hash='x', role='doctor')
    db.add(user)
    db.commit()

case = ClinicalCase(owner_id=1, cattle_tag='C', symptoms='["coughing"]', ai_prediction='Pred', risk_level='medium', status='pending_review', created_at=datetime.utcnow()-timedelta(hours=1))
db.add(case)
db.commit()
db.refresh(case)
print('INITIAL', case.id, case.status, case.veterinarian_id)

outcome = []

def try_claim(vet_id):
    local = Session()
    try:
        result = claim_case_for_veterinarian(case.id, vet_id, local)
        outcome.append((vet_id, result.veterinarian_id, result.status))
        print('SUCCESS', vet_id, result.veterinarian_id, result.status)
    except Exception as exc:
        outcome.append((vet_id, 'error', str(exc)))
        print('FAIL', vet_id, type(exc), exc)
    finally:
        local.close()

threads = [threading.Thread(target=try_claim, args=(1,)), threading.Thread(target=try_claim, args=(2,))]
for t in threads: t.start()
for t in threads: t.join()
print('OUTCOME', outcome)
print('CURRENT DB', db.get(ClinicalCase, case.id).veterinarian_id, db.get(ClinicalCase, case.id).status)
