"""Run-monitor worker: polls the engine, ingests runs, diagnoses new failures.

Run with:  python -m forge.monitor.worker
The compose service `run-monitor` does exactly that. Polling (vs webhooks)
keeps n8n unconfigured and survives missed events; the interval is
MONITOR_POLL_SECONDS.
"""

import logging
import time

from forge.config import get_settings
from forge.db.base import create_db_engine, create_session_factory
from forge.diagnostician import Diagnostician
from forge.engine_adapter import N8nAdapter
from forge.llm_gateway import LLMGateway
from forge.logsetup import configure_logging
from forge.monitor.service import RunMonitor
from forge.registry import WorkflowRegistry

logger = logging.getLogger(__name__)


def poll_once(monitor: RunMonitor, diagnostician: Diagnostician) -> int:
    """One sync + diagnose pass; returns how many new failures were handled."""
    failed_runs = monitor.sync_all()
    for run in failed_runs:
        try:
            incident = diagnostician.diagnose_run(run.id)
            if incident is not None:
                logger.info(
                    "run %s diagnosed → incident %s (%s)",
                    run.engine_execution_id,
                    incident.id,
                    incident.status.value,
                )
        except Exception:
            # One bad diagnosis must not stop the loop or the other runs.
            logger.exception("diagnosis failed for run %s", run.id)
    return len(failed_runs)


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_format)

    engine = create_db_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    adapter = N8nAdapter(settings.n8n_base_url, settings.n8n_api_key)
    gateway = LLMGateway(session_factory, settings)
    registry = WorkflowRegistry(session_factory, adapter)

    monitor = RunMonitor(session_factory, adapter)
    diagnostician = Diagnostician(
        session_factory, gateway, registry, auto_apply=settings.diagnostician_auto_apply
    )

    logger.info("run monitor started (interval: %ss)", settings.monitor_poll_seconds)
    while True:
        try:
            handled = poll_once(monitor, diagnostician)
            if handled:
                logger.info("handled %d new failure(s)", handled)
        except Exception:
            logger.exception("monitor pass failed; retrying next interval")
        time.sleep(settings.monitor_poll_seconds)


if __name__ == "__main__":
    main()
