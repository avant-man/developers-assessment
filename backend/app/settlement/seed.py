import json
import logging
import uuid
from datetime import datetime, timedelta

from sqlmodel import Session, select

from app.core.security import get_password_hash
from app.models import User
from app.settlement import constants as stl_constants
from app.settlement.models import Record

logger = logging.getLogger(__name__)

SEED_WORKERS = [
    {
        "email": "alice@example.com",
        "full_name": "Alice Johnson",
        "password": "worker1234",
    },
    {
        "email": "bob@example.com",
        "full_name": "Bob Smith",
        "password": "worker1234",
    },
    {
        "email": "carol@example.com",
        "full_name": "Carol Williams",
        "password": "worker1234",
    },
]


def seed_settlement_data(session: Session) -> None:
    """
    Populates the database with sample worklogs, segments, adjustments,
    and a couple of existing remittances for demonstration.
    """
    existing = session.exec(
        select(Record).where(Record.type == stl_constants.RECORD_TYPE_WORKLOG)
    ).first()
    if existing:
        logger.info("Settlement seed data already exists, skipping")
        return

    worker_ids = []
    for w in SEED_WORKERS:
        usr = session.exec(select(User).where(User.email == w["email"])).first()
        if not usr:
            usr = User(
                id=uuid.uuid4(),
                email=w["email"],
                full_name=w["full_name"],
                hashed_password=get_password_hash(w["password"]),
                is_active=True,
                is_superuser=False,
            )
            session.add(usr)
            session.commit()
            session.refresh(usr)
        worker_ids.append(usr.id)

    now = datetime.utcnow()

    # --- Alice: 2 worklogs, one fully settled, one unsettled ---
    wl1 = Record(
        type=stl_constants.RECORD_TYPE_WORKLOG,
        user_id=worker_ids[0],
        data=json.dumps({"task_name": "API Integration", "desc": "REST API endpoints for payment gateway"}),
        created_at=now - timedelta(days=30),
    )
    session.add(wl1)
    session.commit()
    session.refresh(wl1)

    seg1 = Record(
        type=stl_constants.RECORD_TYPE_SEGMENT,
        parent_id=wl1.id,
        data=json.dumps({"hrs": 8.0, "rt": 75.0, "desc": "Initial implementation"}),
        created_at=now - timedelta(days=28),
    )
    session.add(seg1)
    session.commit()
    session.refresh(seg1)

    seg2 = Record(
        type=stl_constants.RECORD_TYPE_SEGMENT,
        parent_id=wl1.id,
        data=json.dumps({"hrs": 4.0, "rt": 75.0, "desc": "Code review fixes"}),
        created_at=now - timedelta(days=25),
    )
    session.add(seg2)
    session.commit()
    session.refresh(seg2)

    rmtnc1 = Record(
        type=stl_constants.RECORD_TYPE_REMITTANCE,
        user_id=worker_ids[0],
        data=json.dumps({"ttl_amt": 900.0, "sts": stl_constants.REMITTANCE_STATUS_COMPLETED}),
        created_at=now - timedelta(days=15),
    )
    session.add(rmtnc1)
    session.commit()
    session.refresh(rmtnc1)

    sl1 = Record(
        type=stl_constants.RECORD_TYPE_SETTLEMENT_LINE,
        parent_id=rmtnc1.id,
        data=json.dumps({"rec_id": seg1.id, "amt": 600.0, "rec_type": "segment"}),
        created_at=now - timedelta(days=15),
    )
    session.add(sl1)
    session.commit()

    sl2 = Record(
        type=stl_constants.RECORD_TYPE_SETTLEMENT_LINE,
        parent_id=rmtnc1.id,
        data=json.dumps({"rec_id": seg2.id, "amt": 300.0, "rec_type": "segment"}),
        created_at=now - timedelta(days=15),
    )
    session.add(sl2)
    session.commit()

    wl2 = Record(
        type=stl_constants.RECORD_TYPE_WORKLOG,
        user_id=worker_ids[0],
        data=json.dumps({"task_name": "Database Migration", "desc": "Migrate legacy schema to new format"}),
        created_at=now - timedelta(days=10),
    )
    session.add(wl2)
    session.commit()
    session.refresh(wl2)

    seg3 = Record(
        type=stl_constants.RECORD_TYPE_SEGMENT,
        parent_id=wl2.id,
        data=json.dumps({"hrs": 6.0, "rt": 75.0, "desc": "Schema analysis and planning"}),
        created_at=now - timedelta(days=9),
    )
    session.add(seg3)
    session.commit()

    seg4 = Record(
        type=stl_constants.RECORD_TYPE_SEGMENT,
        parent_id=wl2.id,
        data=json.dumps({"hrs": 10.0, "rt": 75.0, "desc": "Migration scripts"}),
        created_at=now - timedelta(days=7),
    )
    session.add(seg4)
    session.commit()

    adj1 = Record(
        type=stl_constants.RECORD_TYPE_ADJUSTMENT,
        parent_id=wl2.id,
        data=json.dumps({"amt": -50.0, "rsn": "Late delivery penalty"}),
        created_at=now - timedelta(days=5),
    )
    session.add(adj1)
    session.commit()

    # --- Bob: 2 worklogs, both unsettled ---
    wl3 = Record(
        type=stl_constants.RECORD_TYPE_WORKLOG,
        user_id=worker_ids[1],
        data=json.dumps({"task_name": "Frontend Dashboard", "desc": "Build admin dashboard UI"}),
        created_at=now - timedelta(days=20),
    )
    session.add(wl3)
    session.commit()
    session.refresh(wl3)

    seg5 = Record(
        type=stl_constants.RECORD_TYPE_SEGMENT,
        parent_id=wl3.id,
        data=json.dumps({"hrs": 12.0, "rt": 60.0, "desc": "Component development"}),
        created_at=now - timedelta(days=18),
    )
    session.add(seg5)
    session.commit()

    seg6 = Record(
        type=stl_constants.RECORD_TYPE_SEGMENT,
        parent_id=wl3.id,
        data=json.dumps({"hrs": 5.0, "rt": 60.0, "desc": "Styling and responsive design"}),
        created_at=now - timedelta(days=14),
    )
    session.add(seg6)
    session.commit()

    wl4 = Record(
        type=stl_constants.RECORD_TYPE_WORKLOG,
        user_id=worker_ids[1],
        data=json.dumps({"task_name": "Unit Tests", "desc": "Write test suite for dashboard"}),
        created_at=now - timedelta(days=12),
    )
    session.add(wl4)
    session.commit()
    session.refresh(wl4)

    seg7 = Record(
        type=stl_constants.RECORD_TYPE_SEGMENT,
        parent_id=wl4.id,
        data=json.dumps({"hrs": 3.0, "rt": 60.0, "desc": "Test setup and fixtures"}),
        created_at=now - timedelta(days=11),
    )
    session.add(seg7)
    session.commit()

    adj2 = Record(
        type=stl_constants.RECORD_TYPE_ADJUSTMENT,
        parent_id=wl3.id,
        data=json.dumps({"amt": -100.0, "rsn": "Quality rework required"}),
        created_at=now - timedelta(days=10),
    )
    session.add(adj2)
    session.commit()

    # --- Carol: 1 worklog with a failed remittance (should be re-eligible) ---
    wl5 = Record(
        type=stl_constants.RECORD_TYPE_WORKLOG,
        user_id=worker_ids[2],
        data=json.dumps({"task_name": "Documentation", "desc": "API documentation and guides"}),
        created_at=now - timedelta(days=25),
    )
    session.add(wl5)
    session.commit()
    session.refresh(wl5)

    seg8 = Record(
        type=stl_constants.RECORD_TYPE_SEGMENT,
        parent_id=wl5.id,
        data=json.dumps({"hrs": 7.0, "rt": 50.0, "desc": "Write API reference docs"}),
        created_at=now - timedelta(days=23),
    )
    session.add(seg8)
    session.commit()
    session.refresh(seg8)

    seg9 = Record(
        type=stl_constants.RECORD_TYPE_SEGMENT,
        parent_id=wl5.id,
        data=json.dumps({"hrs": 3.0, "rt": 50.0, "desc": "Review and editing"}),
        created_at=now - timedelta(days=20),
    )
    session.add(seg9)
    session.commit()
    session.refresh(seg9)

    rmtnc_failed = Record(
        type=stl_constants.RECORD_TYPE_REMITTANCE,
        user_id=worker_ids[2],
        data=json.dumps({"ttl_amt": 500.0, "sts": stl_constants.REMITTANCE_STATUS_FAILED}),
        created_at=now - timedelta(days=10),
    )
    session.add(rmtnc_failed)
    session.commit()
    session.refresh(rmtnc_failed)

    sl_f1 = Record(
        type=stl_constants.RECORD_TYPE_SETTLEMENT_LINE,
        parent_id=rmtnc_failed.id,
        data=json.dumps({"rec_id": seg8.id, "amt": 350.0, "rec_type": "segment"}),
        created_at=now - timedelta(days=10),
    )
    session.add(sl_f1)
    session.commit()

    sl_f2 = Record(
        type=stl_constants.RECORD_TYPE_SETTLEMENT_LINE,
        parent_id=rmtnc_failed.id,
        data=json.dumps({"rec_id": seg9.id, "amt": 150.0, "rec_type": "segment"}),
        created_at=now - timedelta(days=10),
    )
    session.add(sl_f2)
    session.commit()

    logger.info("Settlement seed data created successfully")
