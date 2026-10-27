import logging
import threading
from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from backend.app.db.session import SessionLocal
from backend.app.db.models.audit import JobRun
from backend.app.services.data_quality_service import data_quality_service
from backend.app.core.logging import logger

job_lock = threading.Lock()

class SchedulerService:
    def __init__(self):
        self.scheduler = BackgroundScheduler(daemon=True)
        self.is_running = False

    def start(self):
        if not self.is_running:
            # Run validation pipeline every 1 hour (and can be triggered on-demand)
            self.scheduler.add_job(
                self.run_validation_job,
                trigger=IntervalTrigger(hours=1),
                id="validation_pipeline",
                name="Data Quality Validation Pipeline",
                replace_existing=True
            )
            self.scheduler.start()
            self.is_running = True
            logger.info("APScheduler local background scheduler started.")

    def shutdown(self):
        if self.is_running:
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            logger.info("APScheduler local background scheduler shut down.")

    def run_validation_job(self) -> JobRun:
        if not job_lock.acquire(blocking=False):
            logger.warning("Validation job already running; skipping duplicate trigger.")
            db = SessionLocal()
            run = JobRun(
                job_name="validation_pipeline",
                started_at=datetime.now(timezone.utc),
                finished_at=datetime.now(timezone.utc),
                status="skipped",
                error_summary="Concurrent run prevented by lock"
            )
            db.add(run)
            db.commit()
            db.close()
            return run

        db: Session = SessionLocal()
        start_time = datetime.now(timezone.utc)
        run = JobRun(
            job_name="validation_pipeline",
            started_at=start_time,
            status="running"
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        try:
            issues = data_quality_service.run_all_checks(db)
            run.status = "success"
            run.finished_at = datetime.now(timezone.utc)
            run.counts = f"Issues detected/updated: {len(issues)}"
            db.commit()
            logger.info("Validation job completed successfully. Detected issues: %d", len(issues))
        except Exception as ex:
            run.status = "failed"
            run.finished_at = datetime.now(timezone.utc)
            run.error_summary = str(ex)
            db.commit()
            logger.error("Validation job failed: %s", ex)
        finally:
            db.close()
            job_lock.release()

        return run

scheduler_service = SchedulerService()
