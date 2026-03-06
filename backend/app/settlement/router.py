import json
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Query
from sqlmodel import select

from app.api.deps import SessionDep
from app.models import User
from app.settlement import constants as stl_constants
from app.settlement.models import Record
from app.settlement.schemas import (
    AdjustmentResponse,
    GenerateRemittancesResponse,
    RemittanceDetail,
    SegmentResponse,
    WorklogListResponse,
    WorklogResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settlement", tags=["settlement"])


def _get_settled_amounts(session: SessionDep, wl_id: int) -> float:
    """
    wl_id: worklog id
    Returns total settled amount for a worklog across active remittances.
    """
    try:
        segs = session.exec(
            select(Record).where(
                Record.type == stl_constants.RECORD_TYPE_SEGMENT,
                Record.parent_id == wl_id,
            )
        ).all()
        adjs = session.exec(
            select(Record).where(
                Record.type == stl_constants.RECORD_TYPE_ADJUSTMENT,
                Record.parent_id == wl_id,
            )
        ).all()

        seg_ids = {s.id for s in segs}
        adj_ids = {a.id for a in adjs}
        all_rec_ids = seg_ids | adj_ids

        if not all_rec_ids:
            return 0.0

        rmtncs = session.exec(
            select(Record).where(
                Record.type == stl_constants.RECORD_TYPE_REMITTANCE,
            )
        ).all()

        active_rmtnc_ids = set()
        for r in rmtncs:
            d = json.loads(r.data)
            if d.get("sts") in stl_constants.REMITTANCE_ACTIVE_STATUSES:
                active_rmtnc_ids.add(r.id)

        if not active_rmtnc_ids:
            return 0.0

        stl_lines = session.exec(
            select(Record).where(
                Record.type == stl_constants.RECORD_TYPE_SETTLEMENT_LINE,
            )
        ).all()

        t = 0.0
        for sl in stl_lines:
            if sl.parent_id not in active_rmtnc_ids:
                continue
            d = json.loads(sl.data)
            if d.get("rec_id") in all_rec_ids:
                t += d.get("amt", 0.0)

        return round(t, 2)
    except Exception as e:
        logger.error(f"Failed to get settled amounts for worklog {wl_id}: {e}")
        return 0.0


def _calc_wl_amount(session: SessionDep, wl_id: int) -> float:
    """
    wl_id: worklog id
    Returns total amount for a worklog (segments + adjustments).
    """
    try:
        segs = session.exec(
            select(Record).where(
                Record.type == stl_constants.RECORD_TYPE_SEGMENT,
                Record.parent_id == wl_id,
            )
        ).all()
        adjs = session.exec(
            select(Record).where(
                Record.type == stl_constants.RECORD_TYPE_ADJUSTMENT,
                Record.parent_id == wl_id,
            )
        ).all()

        t = 0.0
        for s in segs:
            d = json.loads(s.data)
            v = d.get("hrs", 0.0) * d.get("rt", 0.0)
            t += v

        for a in adjs:
            d = json.loads(a.data)
            t += d.get("amt", 0.0)

        return round(t, 2)
    except Exception as e:
        logger.error(f"Failed to calc worklog amount for {wl_id}: {e}")
        return 0.0


@router.post(
    "/generate-remittances-for-all-users",
    response_model=GenerateRemittancesResponse,
)
def generate_remittances_for_all_users(session: SessionDep) -> Any:
    """
    Generates remittances for all users based on eligible (unsettled) work.
    For each user: gathers unsettled segments/adjustments, computes total,
    creates a remittance record with settlement_line entries.
    """
    users = session.exec(select(User)).all()
    created = []

    for usr in users:
        try:
            wls = session.exec(
                select(Record).where(
                    Record.type == stl_constants.RECORD_TYPE_WORKLOG,
                    Record.user_id == usr.id,
                )
            ).all()

            if not wls:
                continue

            active_rmtnc_ids = set()
            all_rmtncs = session.exec(
                select(Record).where(
                    Record.type == stl_constants.RECORD_TYPE_REMITTANCE,
                )
            ).all()
            for r in all_rmtncs:
                d = json.loads(r.data)
                if d.get("sts") in stl_constants.REMITTANCE_ACTIVE_STATUSES:
                    active_rmtnc_ids.add(r.id)

            all_stl_lines = session.exec(
                select(Record).where(
                    Record.type == stl_constants.RECORD_TYPE_SETTLEMENT_LINE,
                )
            ).all()

            settled_rec_ids = set()
            for sl in all_stl_lines:
                if sl.parent_id in active_rmtnc_ids:
                    settled_rec_ids.add(json.loads(sl.data).get("rec_id"))

            unsettled_items = []
            ttl = 0.0

            for wl in wls:
                segs = session.exec(
                    select(Record).where(
                        Record.type == stl_constants.RECORD_TYPE_SEGMENT,
                        Record.parent_id == wl.id,
                    )
                ).all()
                adjs = session.exec(
                    select(Record).where(
                        Record.type == stl_constants.RECORD_TYPE_ADJUSTMENT,
                        Record.parent_id == wl.id,
                    )
                ).all()

                for s in segs:
                    if s.id not in settled_rec_ids:
                        d = json.loads(s.data)
                        v = round(d.get("hrs", 0.0) * d.get("rt", 0.0), 2)
                        unsettled_items.append(
                            {"rec_id": s.id, "amt": v, "rec_type": "segment"}
                        )
                        ttl += v

                for a in adjs:
                    if a.id not in settled_rec_ids:
                        d = json.loads(a.data)
                        v = round(d.get("amt", 0.0), 2)
                        unsettled_items.append(
                            {"rec_id": a.id, "amt": v, "rec_type": "adjustment"}
                        )
                        ttl += v

            ttl = round(ttl, 2)

            if not unsettled_items:
                continue

            rmtnc = Record(
                type=stl_constants.RECORD_TYPE_REMITTANCE,
                user_id=usr.id,
                data=json.dumps(
                    {
                        "ttl_amt": ttl,
                        "sts": stl_constants.REMITTANCE_STATUS_PENDING,
                    }
                ),
                created_at=datetime.utcnow(),
            )
            session.add(rmtnc)
            session.commit()
            session.refresh(rmtnc)

            for item in unsettled_items:
                sl = Record(
                    type=stl_constants.RECORD_TYPE_SETTLEMENT_LINE,
                    parent_id=rmtnc.id,
                    data=json.dumps(item),
                    created_at=datetime.utcnow(),
                )
                session.add(sl)
                session.commit()

            created.append(
                RemittanceDetail(
                    id=rmtnc.id,
                    user_id=str(usr.id),
                    ttl_amt=ttl,
                    sts=stl_constants.REMITTANCE_STATUS_PENDING,
                    created_at=rmtnc.created_at,
                )
            )

        except Exception as e:
            logger.error(f"Failed to generate remittance for user {usr.id}: {e}")
            continue

    return GenerateRemittancesResponse(
        msg=f"Generated {len(created)} remittance(s)",
        cnt=len(created),
        remittances=created,
    )


@router.get("/list-all-worklogs", response_model=WorklogListResponse)
def list_all_worklogs(
    session: SessionDep,
    remittanceStatus: str | None = Query(
        default=None, description="Filter: REMITTED or UNREMITTED"
    ),
) -> Any:
    """
    Lists all worklogs with filtering and amount information.
    remittanceStatus: optional filter (REMITTED / UNREMITTED)
    """
    wls = session.exec(
        select(Record).where(Record.type == stl_constants.RECORD_TYPE_WORKLOG)
    ).all()

    results = []

    for wl in wls:
        try:
            d = json.loads(wl.data)
            amt = _calc_wl_amount(session, wl.id)
            stl_amt = _get_settled_amounts(session, wl.id)

            if amt != 0.0 and abs(amt - stl_amt) < 0.01:
                sts = stl_constants.FILTER_REMITTED
            else:
                sts = stl_constants.FILTER_UNREMITTED

            if remittanceStatus and sts != remittanceStatus:
                continue

            segs = session.exec(
                select(Record).where(
                    Record.type == stl_constants.RECORD_TYPE_SEGMENT,
                    Record.parent_id == wl.id,
                )
            ).all()
            adjs = session.exec(
                select(Record).where(
                    Record.type == stl_constants.RECORD_TYPE_ADJUSTMENT,
                    Record.parent_id == wl.id,
                )
            ).all()

            seg_list = []
            for s in segs:
                sd = json.loads(s.data)
                hrs = sd.get("hrs", 0.0)
                rt = sd.get("rt", 0.0)
                seg_list.append(
                    SegmentResponse(
                        id=s.id,
                        hrs=hrs,
                        rt=rt,
                        amt=round(hrs * rt, 2),
                        desc=sd.get("desc"),
                        created_at=s.created_at,
                    )
                )

            adj_list = []
            for a in adjs:
                ad = json.loads(a.data)
                adj_list.append(
                    AdjustmentResponse(
                        id=a.id,
                        amt=ad.get("amt", 0.0),
                        rsn=ad.get("rsn"),
                        created_at=a.created_at,
                    )
                )

            results.append(
                WorklogResponse(
                    id=wl.id,
                    user_id=str(wl.user_id),
                    task_name=d.get("task_name", ""),
                    desc=d.get("desc"),
                    amt=amt,
                    rmtnc_sts=sts,
                    segments=seg_list,
                    adjustments=adj_list,
                    created_at=wl.created_at,
                )
            )
        except Exception as e:
            logger.error(f"Failed to process worklog {wl.id}: {e}")
            continue

    return WorklogListResponse(data=results, cnt=len(results))
