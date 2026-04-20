from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database import SessionLocal, init_db
from app.services.demo_seed import DEMO_EMAIL, seed_demo_account


def main() -> int:
    password = os.getenv("DEMO_PASSWORD")
    if not password:
        print("DEMO_PASSWORD environment variable is required.", file=sys.stderr)
        return 1
    init_db()
    with SessionLocal() as db:
        result = seed_demo_account(db, password=password)
    print(f"Demo account seeded: {DEMO_EMAIL}")
    for title in result.course_titles:
        print(f"- {title}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
