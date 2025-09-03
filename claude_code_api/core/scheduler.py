"""Background task scheduler for maintenance operations."""

import asyncio
from datetime import datetime, timedelta
from typing import Callable, Optional
import structlog

from .maintenance import run_maintenance_tasks, log_manager

logger = structlog.get_logger()


class TaskScheduler:
    """Simple background task scheduler."""
    
    def __init__(self):
        self.tasks = []
        self.running = False
        self._background_task: Optional[asyncio.Task] = None
    
    def schedule_daily(self, func: Callable, hour: int = 2, minute: int = 0):
        """Schedule a function to run daily at specified time."""
        self.tasks.append({
            "func": func,
            "type": "daily",
            "hour": hour,
            "minute": minute,
            "last_run": None
        })
    
    def schedule_interval(self, func: Callable, hours: int = 0, minutes: int = 0):
        """Schedule a function to run at regular intervals."""
        if hours == 0 and minutes == 0:
            raise ValueError("Must specify at least hours or minutes")
            
        self.tasks.append({
            "func": func,
            "type": "interval",
            "hours": hours,
            "minutes": minutes,
            "last_run": None
        })
    
    async def start(self):
        """Start the background scheduler."""
        if self.running:
            return
            
        self.running = True
        self._background_task = asyncio.create_task(self._run_scheduler())
        logger.info("Task scheduler started", scheduled_tasks=len(self.tasks))
    
    async def stop(self):
        """Stop the background scheduler."""
        self.running = False
        
        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Task scheduler stopped")
    
    async def _run_scheduler(self):
        """Main scheduler loop."""
        try:
            while self.running:
                current_time = datetime.now()
                
                for task in self.tasks:
                    if await self._should_run_task(task, current_time):
                        await self._run_task(task, current_time)
                
                # Sleep for 60 seconds before next check
                await asyncio.sleep(60)
                
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error("Error in task scheduler", error=str(e))
    
    async def _should_run_task(self, task: dict, current_time: datetime) -> bool:
        """Check if a task should be run now."""
        last_run = task.get("last_run")
        
        if task["type"] == "daily":
            # Check if it's time for daily task
            target_time = current_time.replace(
                hour=task["hour"], 
                minute=task["minute"], 
                second=0, 
                microsecond=0
            )
            
            # If target time has passed today and we haven't run today
            if current_time >= target_time:
                if not last_run or last_run.date() < current_time.date():
                    return True
        
        elif task["type"] == "interval":
            # Check if enough time has passed since last run
            interval = timedelta(hours=task["hours"], minutes=task["minutes"])
            
            if not last_run or (current_time - last_run) >= interval:
                return True
        
        return False
    
    async def _run_task(self, task: dict, current_time: datetime):
        """Execute a scheduled task."""
        try:
            func = task["func"]
            task_name = func.__name__ if hasattr(func, '__name__') else str(func)
            
            logger.info("Running scheduled task", task=task_name, time=current_time.isoformat())
            
            # Execute the task
            if asyncio.iscoroutinefunction(func):
                await func()
            else:
                func()
            
            # Update last run time
            task["last_run"] = current_time
            
            logger.info("Scheduled task completed", task=task_name)
            
        except Exception as e:
            logger.error("Error running scheduled task", task=task_name, error=str(e))


# Global scheduler instance
scheduler = TaskScheduler()


async def setup_maintenance_schedule():
    """Setup default maintenance schedule."""
    try:
        # Daily log cleanup at 2:00 AM
        scheduler.schedule_daily(run_maintenance_tasks, hour=2, minute=0)
        
        # Log rotation check every 6 hours
        async def check_log_rotation():
            if log_manager.should_rotate():
                log_manager.rotate_logs()
        
        scheduler.schedule_interval(check_log_rotation, hours=6)
        
        # Start the scheduler
        await scheduler.start()
        
        logger.info("Maintenance schedule configured")
        
    except Exception as e:
        logger.error("Failed to setup maintenance schedule", error=str(e))