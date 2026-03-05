"""ETL pipeline: fetch data from the autochecker API and load it into the database.

The autochecker dashboard API provides two endpoints:
- GET /api/items — lab/task catalog
- GET /api/logs  — anonymized check results (supports ?since= and ?limit= params)

Both require HTTP Basic Auth (email + password from settings).
"""

from datetime import datetime, timezone

import httpx
from sqlmodel import select

from sqlmodel.ext.asyncio.session import AsyncSession

from app.settings import settings


# ---------------------------------------------------------------------------
# Extract — fetch data from the autochecker API
# ---------------------------------------------------------------------------


async def fetch_items() -> list[dict]:
    """Fetch the lab/task catalog from the autochecker API.

    TODO: Implement this function.
    - Use httpx.AsyncClient to GET {settings.autochecker_api_url}/api/items
    - Pass HTTP Basic Auth using settings.autochecker_email and
      settings.autochecker_password
    - The response is a JSON array of objects with keys:
      lab (str), task (str | null), title (str), type ("lab" | "task")
    - Return the parsed list of dicts
    - Raise an exception if the response status is not 200
    """
    url = f"{settings.autochecker_api_url}/api/items"
    async with httpx.AsyncClient(
        auth=(settings.autochecker_email, settings.autochecker_password)
    ) as client:
        response = await client.get(url)
    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to fetch items: {response.status_code} {response.text}"
        )
    return response.json()


async def fetch_logs(since: datetime | None = None) -> list[dict]:
    """Fetch check results from the autochecker API.

    TODO: Implement this function.
    - Use httpx.AsyncClient to GET {settings.autochecker_api_url}/api/logs
    - Pass HTTP Basic Auth using settings.autochecker_email and
      settings.autochecker_password
    - Query parameters:
      - limit=500 (fetch in batches)
      - since={iso timestamp} if provided (for incremental sync)
    - The response JSON has shape:
      {"logs": [...], "count": int, "has_more": bool}
    - Handle pagination: keep fetching while has_more is True
      - Use the submitted_at of the last log as the new "since" value
    - Return the combined list of all log dicts from all pages
    """
    url = f"{settings.autochecker_api_url}/api/logs"
    logs: list[dict] = []
    params: dict[str, str | int] = {"limit": 500}
    if since is not None:
        if since.tzinfo is None:
            since = since.replace(tzinfo=timezone.utc)
        params["since"] = since.isoformat().replace("+00:00", "Z")

    async with httpx.AsyncClient(
        auth=(settings.autochecker_email, settings.autochecker_password)
    ) as client:
        while True:
            response = await client.get(url, params=params)
            if response.status_code != 200:
                raise RuntimeError(
                    f"Failed to fetch logs: {response.status_code} {response.text}"
                )
            payload = response.json()
            page_logs = payload.get("logs", [])
            logs.extend(page_logs)

            if not payload.get("has_more"):
                break

            if not page_logs:
                break

            last_submitted_at = page_logs[-1].get("submitted_at")
            if last_submitted_at:
                params["since"] = last_submitted_at
            else:
                break

    return logs


# ---------------------------------------------------------------------------
# Load — insert fetched data into the local database
# ---------------------------------------------------------------------------


async def load_items(items: list[dict], session: AsyncSession) -> int:
    """Load items (labs and tasks) into the database.

    TODO: Implement this function.
    - Import ItemRecord from app.models.item
    - Process labs first (items where type="lab"):
      - For each lab, check if an item with type="lab" and matching title
        already exists (SELECT)
      - If not, INSERT a new ItemRecord(type="lab", title=lab_title)
    - Then process tasks (items where type="task"):
      - Find the parent lab item by matching the lab field to a lab's title
      - Check if a task with this title and parent_id already exists
      - If not, INSERT a new ItemRecord(type="task", title=task_title,
        parent_id=lab_item.id)
    - Commit after all inserts
    - Return the number of newly created items
    """
    from app.models.item import ItemRecord

    created = 0

    labs = [item for item in items if item.get("type") == "lab"]
    tasks = [item for item in items if item.get("type") == "task"]

    for item in labs:
        lab_title = item.get("title")
        if not lab_title:
            continue
        statement = select(ItemRecord).where(
            ItemRecord.type == "lab", ItemRecord.title == lab_title
        )
        existing = (await session.exec(statement)).first()
        if existing is None:
            session.add(ItemRecord(type="lab", title=lab_title))
            await session.flush()
            created += 1

    for item in tasks:
        task_title = item.get("title")
        lab_name = item.get("lab")
        if not task_title or not lab_name:
            continue

        lab_statement = select(ItemRecord).where(
            ItemRecord.type == "lab", ItemRecord.title == lab_name
        )
        lab_item = (await session.exec(lab_statement)).first()

        if lab_item is None:
            continue

        task_statement = select(ItemRecord).where(
            ItemRecord.type == "task",
            ItemRecord.title == task_title,
            ItemRecord.parent_id == lab_item.id,
        )
        existing = (await session.exec(task_statement)).first()
        if existing is None:
            session.add(
                ItemRecord(type="task", title=task_title, parent_id=lab_item.id)
            )
            await session.flush()
            created += 1

    await session.commit()
    return created


async def load_logs(logs: list[dict], session: AsyncSession) -> int:
    """Load interaction logs into the database.

    TODO: Implement this function.
    - Import Learner from app.models.learner
    - Import InteractionLog from app.models.interaction
    - Import ItemRecord from app.models.item
    - For each log dict:
      1. Find or create a Learner by external_id (log["student_id"])
         - If creating, set student_group from log["group"]
      2. Find the matching item:
         - If log["task"] is not None, find the task item by title
         - Otherwise, find the lab item by title (from log["lab"])
         - Skip this log if no matching item is found
      3. Check if an InteractionLog with this external_id already exists
         (for idempotent upsert — skip if it does)
      4. Create InteractionLog with:
         - external_id = log["id"]
         - learner_id = learner.id
         - item_id = item.id
         - kind = "attempt"
         - score = log["score"]
         - checks_passed = log["passed"]
         - checks_total = log["total"]
         - created_at = parsed log["submitted_at"]
    - Commit after all inserts
    - Return the number of newly created interactions
    """
    from app.models.interaction import InteractionLog
    from app.models.item import ItemRecord
    from app.models.learner import Learner

    created = 0

    for log in logs:
        student_id = log.get("student_id")
        if not student_id:
            continue

        learner_statement = select(Learner).where(Learner.external_id == student_id)
        learner = (await session.exec(learner_statement)).first()
        if learner is None:
            learner = Learner(
                external_id=student_id, student_group=log.get("group", "")
            )
            session.add(learner)
            await session.flush()

        item = None
        task_title = log.get("task")
        if task_title:
            item_statement = select(ItemRecord).where(
                ItemRecord.type == "task", ItemRecord.title == task_title
            )
            item = (await session.exec(item_statement)).first()
        else:
            lab_title = log.get("lab")
            if lab_title:
                item_statement = select(ItemRecord).where(
                    ItemRecord.type == "lab", ItemRecord.title == lab_title
                )
                item = (await session.exec(item_statement)).first()

        if item is None:
            continue

        external_id = log.get("id")
        interaction_statement = select(InteractionLog).where(
            InteractionLog.external_id == external_id
        )
        existing = (await session.exec(interaction_statement)).first()
        if existing is not None:
            continue

        submitted_at = log.get("submitted_at")
        if submitted_at:
            parsed_submitted_at = datetime.fromisoformat(
                submitted_at.replace("Z", "+00:00")
            ).astimezone(timezone.utc)
            created_at = parsed_submitted_at.replace(tzinfo=None)
        else:
            created_at = datetime.now(timezone.utc).replace(tzinfo=None)

        interaction = InteractionLog(
            external_id=external_id,
            learner_id=learner.id,
            item_id=item.id,
            kind="attempt",
            score=log.get("score"),
            checks_passed=log.get("passed"),
            checks_total=log.get("total"),
            created_at=created_at,
        )
        session.add(interaction)
        await session.flush()
        created += 1

    await session.commit()
    return created


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


async def sync(session: AsyncSession) -> dict:
    """Run the full ETL pipeline.

    TODO: Implement this function.
    - Step 1: Fetch items from the API and load them into the database
    - Step 2: Determine the last synced timestamp
      - Query the most recent created_at from InteractionLog
      - If no records exist, since=None (fetch everything)
    - Step 3: Fetch logs since that timestamp and load them
    - Return a dict: {"new_records": <number of new interactions>,
                      "total_records": <total interactions in DB>}
    """
    from sqlalchemy import func

    from app.models.interaction import InteractionLog

    items = await fetch_items()
    await load_items(items, session)

    last_statement = (
        select(InteractionLog.created_at)
        .order_by(InteractionLog.created_at.desc())
        .limit(1)
    )
    last_result = await session.exec(last_statement)
    last_created_at = last_result.first()
    if isinstance(last_created_at, tuple):
        last_created_at = last_created_at[0]

    logs = await fetch_logs(last_created_at)
    new_records = await load_logs(logs, session)

    count_result = await session.exec(
        select(func.count()).select_from(InteractionLog)
    )
    count_row = count_result.one()
    total_records = count_row if isinstance(count_row, int) else count_row[0]

    return {"new_records": new_records, "total_records": total_records}
