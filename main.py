"""
Run this to start the daily news pipeline or the scheduler.
"""

import asyncio
import argparse
from scheduler.runner import start_scheduler
from graph.pipeline import run_pipeline


def main():
    parser = argparse.ArgumentParser(description="AI News Intelligence Agent")
    parser.add_argument(
        "--mode",
        choices=["run", "schedule"],
        default="run",
        help="run: execute once now | schedule: start daily scheduler",
    )
    parser.add_argument(
        "--query",
        type=str,
        default="Artificial Intelligence",
        help="News search query (default: 'Artificial Intelligence')",
    )
    args = parser.parse_args()

    if args.mode == "run":
        print("🚀 Running news intelligence pipeline...")
        asyncio.run(run_pipeline(query=args.query))
    elif args.mode == "schedule":
        print("📅 Starting daily scheduler...")
        start_scheduler(query=args.query)


if __name__ == "__main__":
    main()
