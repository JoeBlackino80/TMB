"""Denná údržba (spúšťa cron): vypne vypršané trialy a upratuje
neoverené účty staršie než UNVERIFIED_DAYS dní.

Používanie: python -m webapp.expire
"""

from datetime import datetime, timedelta

from . import clientfs
from .auth import Users

# po koľkých dňoch bez potvrdenia e-mailu sa účet vypne
UNVERIFIED_DAYS = 7


def _stale_unverified(user) -> bool:
    if user["verified"]:
        return False
    try:
        created = datetime.fromisoformat(user["created_at"])
    except (ValueError, TypeError):
        return False
    return created < datetime.now() - timedelta(days=UNVERIFIED_DAYS)


def main() -> None:
    users = Users()
    try:
        for user in users.all():
            enabled = users.is_service_enabled(user)
            if user["status"] == "trial" and not enabled:
                users.set_status(user["id"], "expired")
                print(f"Trial vypršal: {user['email']}")
            if _stale_unverified(user):
                enabled = False
                print(f"Neoverený {UNVERIFIED_DAYS}+ dní: {user['email']}")
            clientfs.set_enabled(user["client_dir"], enabled)
    finally:
        users.close()


if __name__ == "__main__":
    main()
