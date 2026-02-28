"""Placeholder Prefect flow scaffold for future orchestration."""

from datetime import datetime

from prefect import flow


@flow(name="pharma-data-hub-placeholder")
def placeholder_flow() -> str:
    return f"Prefect scaffold active at {datetime.utcnow().isoformat()}Z"


if __name__ == "__main__":
    print(placeholder_flow())
