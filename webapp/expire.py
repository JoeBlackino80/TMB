"""Denná údržba: vypne klientov s vypršaným trialom (spúšťa cron).

Používanie: python -m webapp.expire
"""

from . import clientfs
from .auth import Users


def main() -> None:
    users = Users()
    try:
        for user in users.all():
            enabled = users.is_service_enabled(user)
            if user["status"] == "trial" and not enabled:
                users.set_status(user["id"], "expired")
                print(f"Trial vypršal: {user['email']}")
            clientfs.set_enabled(user["client_dir"], enabled)
    finally:
        users.close()


if __name__ == "__main__":
    main()
