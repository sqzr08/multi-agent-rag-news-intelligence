"""
Scheduler — runs the full pipeline once per day at a configured time.
Uses APScheduler with an AsyncIOScheduler.
"""

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

import config
from graph.pipeline import run_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def scheduled_job(query: str) -> None:
    logger.info("⏰ Scheduled run triggered")
    try:
        await run_pipeline(query=query)
        logger.info("✅ Scheduled run completed")
    except Exception as e:
        logger.error(f"❌ Scheduled run failed: {e}", exc_info=True)


def start_scheduler(query: str = "Artificial Intelligence") -> None:
    """Start the APScheduler and block until interrupted."""
    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        scheduled_job,
        trigger=CronTrigger(
            hour=config.SCHEDULE_HOUR,
            minute=config.SCHEDULE_MINUTE,
        ),
        args=[query],
        id="daily_news_pipeline",
        name="Daily AI News Intelligence",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        f"📅 Scheduler started — pipeline runs daily at "
        f"{config.SCHEDULE_HOUR:02d}:{config.SCHEDULE_MINUTE:02d}"
    )

    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Scheduler stopped.")
