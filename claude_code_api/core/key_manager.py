"""Claude API Key rotation and management."""

import asyncio
import json
import os
import time
from typing import List, Dict, Optional, Any
import structlog

logger = structlog.get_logger()


class ClaudeKeyManager:
    """Manages Claude API key rotation and failover."""
    
    def __init__(self, keys_config: str):
        """Initialize with keys configuration from environment."""
        self.keys: List[Dict[str, Any]] = []
        self.current_index = 0
        self.last_rotation_time = 0
        self.failed_keys = set()
        
        try:
            # Parse keys from JSON string
            if keys_config:
                self.keys = json.loads(keys_config)
                logger.info("Loaded API keys", count=len(self.keys))
            else:
                logger.warning("No API keys configuration found")
                
        except json.JSONDecodeError as e:
            logger.error("Failed to parse API keys configuration", error=str(e))
            self.keys = []
    
    def get_current_key(self) -> Optional[Dict[str, Any]]:
        """Get the currently active API key."""
        if not self.keys:
            return None
            
        # Skip failed keys
        attempts = 0
        while attempts < len(self.keys):
            key = self.keys[self.current_index]
            if self.current_index not in self.failed_keys:
                return key
            
            # Move to next key
            self.current_index = (self.current_index + 1) % len(self.keys)
            attempts += 1
        
        # All keys failed, reset and try again
        if self.failed_keys:
            logger.warning("All keys failed, resetting failed keys list")
            self.failed_keys.clear()
            return self.keys[self.current_index] if self.keys else None
            
        return None
    
    def mark_key_failed(self, reason: str = "unknown") -> bool:
        """Mark current key as failed and rotate to next."""
        if not self.keys:
            return False
            
        current_key = self.keys[self.current_index]
        self.failed_keys.add(self.current_index)
        
        logger.warning(
            "Marking API key as failed",
            key_name=current_key.get('name', 'unnamed'),
            key_index=self.current_index,
            reason=reason,
            failed_count=len(self.failed_keys)
        )
        
        # Rotate to next key
        success = self.rotate_key()
        
        # Apply the new key to environment and config files
        if success:
            self.apply_current_key()
        
        # Trigger process restart if configured
        if success and self._should_restart_on_rotate():
            try:
                # Check if there's a running event loop
                loop = asyncio.get_running_loop()
                asyncio.create_task(self._restart_process())
            except RuntimeError:
                # No event loop running, skip restart (this is normal in testing)
                logger.info("No event loop running, skipping process restart")
        
        return success
    
    def _should_restart_on_rotate(self) -> bool:
        """Check if process should be restarted after key rotation."""
        try:
            from .config import settings
            return getattr(settings, 'claude_restart_on_rotate', False)
        except ImportError:
            return False
    
    async def _restart_process(self):
        """Restart the server process after key rotation."""
        try:
            from .maintenance import process_manager
            
            logger.info("Initiating process restart due to key rotation")
            
            # Wait a bit to let current requests finish
            await asyncio.sleep(2)
            
            success = await process_manager.restart_server()
            if success:
                logger.info("Process restart completed successfully")
            else:
                logger.error("Process restart failed")
                
        except Exception as e:
            logger.error("Error during process restart", error=str(e))
    
    def rotate_key(self) -> bool:
        """Rotate to the next available key."""
        if not self.keys:
            return False
            
        old_index = self.current_index
        self.current_index = (self.current_index + 1) % len(self.keys)
        self.last_rotation_time = time.time()
        
        new_key = self.get_current_key()
        if new_key:
            logger.info(
                "Rotated API key",
                from_index=old_index,
                to_index=self.current_index,
                new_key_name=new_key.get('name', 'unnamed'),
                total_keys=len(self.keys)
            )
            return True
        else:
            logger.error("No available keys for rotation")
            return False
    
    def apply_current_key(self) -> bool:
        """Apply the current key to environment variables and update shell config files."""
        key = self.get_current_key()
        if not key:
            logger.error("No available API key to apply")
            return False
            
        try:
            # Set environment variables that Claude CLI uses
            os.environ['ANTHROPIC_AUTH_TOKEN'] = key['token']
            if 'base_url' in key:
                os.environ['ANTHROPIC_BASE_URL'] = key['base_url']
            
            # Update shell configuration files
            self._update_shell_config_files(key['token'])
            
            logger.info(
                "Applied API key to environment and config files",
                key_name=key.get('name', 'unnamed'),
                key_index=self.current_index,
                base_url=key.get('base_url', 'default')
            )
            return True
            
        except Exception as e:
            logger.error("Failed to apply API key", error=str(e))
            return False
    
    def _update_shell_config_files(self, new_token: str):
        """Update ANTHROPIC_AUTH_TOKEN in shell configuration files."""
        import os.path
        import subprocess
        
        # List of shell configuration files to update
        config_files = [
            os.path.expanduser("~/.bash_profile"),
            os.path.expanduser("~/.bashrc"),
            os.path.expanduser("~/.zshrc")
        ]
        
        for config_file in config_files:
            try:
                if os.path.exists(config_file):
                    # Check if ANTHROPIC_AUTH_TOKEN exists in the file
                    with open(config_file, 'r') as f:
                        content = f.read()
                    
                    if 'ANTHROPIC_AUTH_TOKEN' in content:
                        # Use sed to replace the existing token
                        subprocess.run([
                            'sed', '-i', 
                            f's/export ANTHROPIC_AUTH_TOKEN=.*/export ANTHROPIC_AUTH_TOKEN={new_token}/',
                            config_file
                        ], check=True)
                        logger.info(f"Updated ANTHROPIC_AUTH_TOKEN in {config_file}")
                    else:
                        # Add the token if it doesn't exist
                        with open(config_file, 'a') as f:
                            f.write(f'\nexport ANTHROPIC_AUTH_TOKEN={new_token}\n')
                        logger.info(f"Added ANTHROPIC_AUTH_TOKEN to {config_file}")
                        
            except Exception as e:
                logger.warning(f"Failed to update {config_file}", error=str(e))
        
        logger.info("Shell configuration files updated with new API key")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current key manager status."""
        current_key = self.get_current_key()
        
        return {
            "total_keys": len(self.keys),
            "current_index": self.current_index,
            "current_key_name": current_key.get('name', 'unnamed') if current_key else None,
            "failed_keys": len(self.failed_keys),
            "available_keys": len(self.keys) - len(self.failed_keys),
            "last_rotation": self.last_rotation_time,
            "keys_status": [
                {
                    "index": i,
                    "name": key.get('name', f'key_{i}'),
                    "status": key.get('status', 'active') if i not in self.failed_keys else "failed",
                    "current": i == self.current_index
                }
                for i, key in enumerate(self.keys)
            ]
        }


def detect_claude_error(stderr_output: str) -> Optional[str]:
    """Detect Claude API errors from stderr output."""
    if not stderr_output:
        return None
        
    stderr_lower = stderr_output.lower()
    
    # Common error patterns
    error_patterns = {
        "insufficient_quota": ["insufficient quota", "quota exceeded", "billing", "usage limit"],
        "rate_limit": ["rate limit", "too many requests", "throttle"],
        "auth_error": ["authentication", "invalid api key", "unauthorized"],
        "server_error": ["internal server error", "service unavailable", "timeout"]
    }
    
    for error_type, patterns in error_patterns.items():
        if any(pattern in stderr_lower for pattern in patterns):
            return error_type
    
    return None


# Global key manager instance to maintain state across requests
_global_key_manager: Optional[ClaudeKeyManager] = None


def create_key_manager_from_config() -> Optional[ClaudeKeyManager]:
    """Get or create key manager from environment configuration (singleton pattern)."""
    global _global_key_manager
    
    if _global_key_manager is not None:
        return _global_key_manager
    
    from .config import settings
    
    keys_config = getattr(settings, 'claude_api_keys', '')
    if not keys_config:
        logger.warning("No Claude API keys configuration found in settings")
        return None
    
    _global_key_manager = ClaudeKeyManager(keys_config)
    logger.info("Created global key manager instance")
    return _global_key_manager


def reset_key_manager():
    """Reset global key manager (for testing purposes)."""
    global _global_key_manager
    _global_key_manager = None