"""Log rotation and cleanup utilities."""

import os
import time
import shutil
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import structlog

logger = structlog.get_logger()


class LogManager:
    """Manages log rotation, cleanup, and archiving."""
    
    def __init__(self, log_file: str = "claude_api.log", max_size_mb: int = 50, keep_days: int = 7):
        self.log_file = Path(log_file)
        self.max_size_mb = max_size_mb
        self.keep_days = keep_days
        self.log_dir = self.log_file.parent / "logs"
        self.log_dir.mkdir(exist_ok=True)
    
    def should_rotate(self) -> bool:
        """Check if log rotation is needed."""
        if not self.log_file.exists():
            return False
            
        # Check file size
        size_mb = self.log_file.stat().st_size / (1024 * 1024)
        return size_mb > self.max_size_mb
    
    def rotate_logs(self) -> bool:
        """Rotate current log file and create archive."""
        try:
            if not self.log_file.exists():
                return True
            
            # Create timestamp for archived log
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archived_log = self.log_dir / f"claude_api_{timestamp}.log"
            
            # Move current log to archive
            shutil.move(str(self.log_file), str(archived_log))
            
            # Compress archived log to save space
            await self._compress_log(archived_log)
            
            logger.info(
                "Log rotated successfully",
                archived_file=str(archived_log),
                timestamp=timestamp
            )
            
            return True
            
        except Exception as e:
            logger.error("Failed to rotate logs", error=str(e))
            return False
    
    async def _compress_log(self, log_path: Path) -> bool:
        """Compress log file using gzip."""
        try:
            import gzip
            
            compressed_path = log_path.with_suffix('.log.gz')
            
            with open(log_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove uncompressed file
            log_path.unlink()
            
            logger.info("Log compressed", compressed_file=str(compressed_path))
            return True
            
        except Exception as e:
            logger.error("Failed to compress log", error=str(e))
            return False
    
    def cleanup_old_logs(self) -> int:
        """Remove log files older than keep_days."""
        try:
            cutoff_time = time.time() - (self.keep_days * 24 * 60 * 60)
            removed_count = 0
            
            for log_file in self.log_dir.glob("claude_api_*.log*"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    removed_count += 1
                    logger.info("Removed old log file", file=str(log_file))
            
            if removed_count > 0:
                logger.info("Cleaned up old logs", removed_count=removed_count)
            
            return removed_count
            
        except Exception as e:
            logger.error("Failed to cleanup old logs", error=str(e))
            return 0
    
    def get_log_stats(self) -> dict:
        """Get statistics about log files."""
        try:
            stats = {
                "current_log_size_mb": 0,
                "archived_logs": 0,
                "total_archived_size_mb": 0,
                "oldest_log_age_days": 0
            }
            
            # Current log size
            if self.log_file.exists():
                stats["current_log_size_mb"] = round(
                    self.log_file.stat().st_size / (1024 * 1024), 2
                )
            
            # Archived logs
            archived_files = list(self.log_dir.glob("claude_api_*.log*"))
            stats["archived_logs"] = len(archived_files)
            
            if archived_files:
                total_size = sum(f.stat().st_size for f in archived_files)
                stats["total_archived_size_mb"] = round(total_size / (1024 * 1024), 2)
                
                oldest_file = min(archived_files, key=lambda f: f.stat().st_mtime)
                age_days = (time.time() - oldest_file.stat().st_mtime) / (24 * 60 * 60)
                stats["oldest_log_age_days"] = round(age_days, 1)
            
            return stats
            
        except Exception as e:
            logger.error("Failed to get log stats", error=str(e))
            return {}


class ProcessManager:
    """Manages server process restarts and health checks."""
    
    def __init__(self, pid_file: str = "claude_api.pid"):
        self.pid_file = Path(pid_file)
    
    def get_current_pid(self) -> Optional[int]:
        """Get the current server PID."""
        try:
            if self.pid_file.exists():
                with open(self.pid_file, 'r') as f:
                    return int(f.read().strip())
            return None
        except (ValueError, FileNotFoundError):
            return None
    
    def is_process_running(self, pid: int) -> bool:
        """Check if a process is running."""
        try:
            import psutil
            return psutil.pid_exists(pid)
        except ImportError:
            # Fallback: use kill -0 to check if process exists
            try:
                os.kill(pid, 0)
                return True
            except (OSError, ProcessLookupError):
                return False
    
    async def restart_server(self) -> bool:
        """Restart the API server gracefully."""
        try:
            current_pid = self.get_current_pid()
            
            if current_pid and self.is_process_running(current_pid):
                logger.info("Stopping current server", pid=current_pid)
                
                # Graceful shutdown first
                try:
                    os.kill(current_pid, 15)  # SIGTERM
                    await asyncio.sleep(5)  # Wait for graceful shutdown
                    
                    if self.is_process_running(current_pid):
                        logger.warning("Graceful shutdown failed, forcing stop", pid=current_pid)
                        os.kill(current_pid, 9)  # SIGKILL
                        await asyncio.sleep(2)
                        
                except (OSError, ProcessLookupError):
                    pass  # Process already dead
            
            # Start new server
            logger.info("Starting new server process")
            
            # Execute make start-prod-bg
            process = await asyncio.create_subprocess_exec(
                "make", "start-prod-bg",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info("Server restarted successfully")
                return True
            else:
                logger.error("Failed to restart server", error=stderr.decode())
                return False
                
        except Exception as e:
            logger.error("Error during server restart", error=str(e))
            return False
    
    async def health_check(self) -> dict:
        """Perform health check on the server."""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get('http://localhost:8010/health', timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "status": "healthy",
                            "response_time_ms": response.headers.get("X-Response-Time", "unknown"),
                            "data": data
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "http_status": response.status
                        }
                        
        except Exception as e:
            return {
                "status": "unreachable",
                "error": str(e)
            }


# Global instances
log_manager = LogManager()
process_manager = ProcessManager()


async def run_maintenance_tasks():
    """Run periodic maintenance tasks."""
    logger.info("Starting maintenance tasks")
    
    try:
        # Log rotation
        if log_manager.should_rotate():
            log_manager.rotate_logs()
        
        # Cleanup old logs
        removed_logs = log_manager.cleanup_old_logs()
        
        # Health check
        health = await process_manager.health_check()
        logger.info("Health check completed", health_status=health.get("status"))
        
        logger.info("Maintenance tasks completed", removed_logs=removed_logs)
        
    except Exception as e:
        logger.error("Error in maintenance tasks", error=str(e))