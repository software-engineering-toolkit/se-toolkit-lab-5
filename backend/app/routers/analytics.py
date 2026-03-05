"""Router for analytics endpoints.

Each endpoint performs SQL aggregation queries on the interaction data
populated by the ETL pipeline. All endpoints require a `lab` query
parameter to filter results by lab (e.g., "lab-01").
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, distinct, func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models.interaction import InteractionLog
from app.models.item import ItemRecord
from app.models.learner import Learner

router = APIRouter()


async def _get_lab_and_tasks(session: AsyncSession, lab: str) -> tuple[ItemRecord | None, list[ItemRecord]]:
    lab_title = lab.replace("-", " ").title()
    lab_result = await session.exec(
        select(ItemRecord).where(
            ItemRecord.type == "lab",
            func.lower(ItemRecord.title).contains(lab_title.lower()),
        )
    )
    lab_item = lab_result.first()
    if lab_item is None:
        return None, []

    tasks_result = await session.exec(
        select(ItemRecord).where(
            ItemRecord.type == "task",
            ItemRecord.parent_id == lab_item.id,
        )
    )
    return lab_item, list(tasks_result.all())


@router.get("/scores")
async def get_scores(
    lab: str = Query(..., description="Lab identifier, e.g. 'lab-01'"),
    session: AsyncSession = Depends(get_session),
):
    """Score distribution histogram for a given lab.

    TODO: Implement this endpoint.
    - Find the lab item by matching title (contains the lab identifier)
    - Find all tasks that belong to this lab (parent_id = lab.id)
    - Query interactions for these items that have a score
    - Group scores into buckets: "0-25", "26-50", "51-75", "76-100"
      using CASE WHEN expressions
    - Return a JSON array:
      [{"bucket": "0-25", "count": 12}, {"bucket": "26-50", "count": 8}, ...]
    - Always return all four buckets, even if count is 0
    """
    _lab, tasks = await _get_lab_and_tasks(session, lab)
    if not tasks:
        return [
            {"bucket": "0-25", "count": 0},
            {"bucket": "26-50", "count": 0},
            {"bucket": "51-75", "count": 0},
            {"bucket": "76-100", "count": 0},
        ]

    task_ids = [task.id for task in tasks if task.id is not None]

    bucket = case(
        (InteractionLog.score <= 25, "0-25"),
        (InteractionLog.score <= 50, "26-50"),
        (InteractionLog.score <= 75, "51-75"),
        else_="76-100",
    ).label("bucket")

    result = await session.exec(
        select(bucket, func.count().label("count"))
        .where(
            InteractionLog.item_id.in_(task_ids),
            InteractionLog.score.is_not(None),
        )
        .group_by(bucket)
    )
    counts = {row.bucket: row.count for row in result.all()}

    return [
        {"bucket": "0-25", "count": counts.get("0-25", 0)},
        {"bucket": "26-50", "count": counts.get("26-50", 0)},
        {"bucket": "51-75", "count": counts.get("51-75", 0)},
        {"bucket": "76-100", "count": counts.get("76-100", 0)},
    ]


@router.get("/pass-rates")
async def get_pass_rates(
    lab: str = Query(..., description="Lab identifier, e.g. 'lab-01'"),
    session: AsyncSession = Depends(get_session),
):
    """Per-task pass rates for a given lab.

    TODO: Implement this endpoint.
    - Find the lab item and its child task items
    - For each task, compute:
      - avg_score: average of interaction scores (round to 1 decimal)
      - attempts: total number of interactions
    - Return a JSON array:
      [{"task": "Repository Setup", "avg_score": 92.3, "attempts": 150}, ...]
    - Order by task title
    """
    _lab, tasks = await _get_lab_and_tasks(session, lab)
    if not tasks:
        return []

    result = await session.exec(
        select(
            ItemRecord.title.label("task"),
            func.avg(InteractionLog.score).label("avg_score"),
            func.count(InteractionLog.id).label("attempts"),
        )
        .where(
            ItemRecord.type == "task",
            ItemRecord.id.in_([task.id for task in tasks if task.id is not None]),
        )
        .join(InteractionLog, InteractionLog.item_id == ItemRecord.id, isouter=True)
        .group_by(ItemRecord.id)
        .order_by(ItemRecord.title)
    )

    response = []
    for row in result.all():
        avg_score = 0.0 if row.avg_score is None else round(float(row.avg_score), 1)
        response.append(
            {
                "task": row.task,
                "avg_score": avg_score,
                "attempts": int(row.attempts or 0),
            }
        )
    return response


@router.get("/timeline")
async def get_timeline(
    lab: str = Query(..., description="Lab identifier, e.g. 'lab-01'"),
    session: AsyncSession = Depends(get_session),
):
    """Submissions per day for a given lab.

    TODO: Implement this endpoint.
    - Find the lab item and its child task items
    - Group interactions by date (created_at::date)
    - Count the number of submissions per day
    - Return a JSON array:
      [{"date": "2026-02-28", "submissions": 45}, ...]
    - Order by date ascending
    """
    _lab, tasks = await _get_lab_and_tasks(session, lab)
    if not tasks:
        return []

    task_ids = [task.id for task in tasks if task.id is not None]
    date_bucket = func.date(InteractionLog.created_at).label("date")

    result = await session.exec(
        select(
            date_bucket,
            func.count(InteractionLog.id).label("submissions"),
        )
        .where(InteractionLog.item_id.in_(task_ids))
        .group_by(date_bucket)
        .order_by(date_bucket)
    )

    return [
        {"date": str(row.date), "submissions": int(row.submissions)}
        for row in result.all()
    ]


@router.get("/groups")
async def get_groups(
    lab: str = Query(..., description="Lab identifier, e.g. 'lab-01'"),
    session: AsyncSession = Depends(get_session),
):
    """Per-group performance for a given lab.

    TODO: Implement this endpoint.
    - Find the lab item and its child task items
    - Join interactions with learners to get student_group
    - For each group, compute:
      - avg_score: average score (round to 1 decimal)
      - students: count of distinct learners
    - Return a JSON array:
      [{"group": "B23-CS-01", "avg_score": 78.5, "students": 25}, ...]
    - Order by group name
    """
    _lab, tasks = await _get_lab_and_tasks(session, lab)
    if not tasks:
        return []

    task_ids = [task.id for task in tasks if task.id is not None]

    result = await session.exec(
        select(
            Learner.student_group.label("group"),
            func.avg(InteractionLog.score).label("avg_score"),
            func.count(distinct(InteractionLog.learner_id)).label("students"),
        )
        .where(InteractionLog.item_id.in_(task_ids))
        .join(Learner, Learner.id == InteractionLog.learner_id)
        .group_by(Learner.student_group)
        .order_by(Learner.student_group)
    )

    response = []
    for row in result.all():
        avg_score = 0.0 if row.avg_score is None else round(float(row.avg_score), 1)
        response.append(
            {
                "group": row.group,
                "avg_score": avg_score,
                "students": int(row.students or 0),
            }
        )
    return response
