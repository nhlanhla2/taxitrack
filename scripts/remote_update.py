#!/usr/bin/env python3
"""
Remote Update Manager for Taxi Streaming System
Handles git-based updates with minimal downtime
"""

import os
import sys
import subprocess
import time
import requests
import logging
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RemoteUpdater:
    def __init__(self, repo_url: str, branch: str = "main"):
        self.repo_url = repo_url
        self.branch = branch
        self.app_dir = Path("/app")
        self.service_url = "http://localhost:8000"
        
    def check_service_health(self) -> bool:
        """Check if the service is running"""
        try:
            response = requests.get(f"{self.service_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_current_commit(self) -> Optional[str]:
        """Get current git commit hash"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.app_dir,
                capture_output=True,
                text=True
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except:
            return None
    
    def get_remote_commit(self) -> Optional[str]:
        """Get remote git commit hash"""
        try:
            subprocess.run(["git", "fetch", "origin"], cwd=self.app_dir, check=True)
            result = subprocess.run(
                ["git", "rev-parse", f"origin/{self.branch}"],
                cwd=self.app_dir,
                capture_output=True,
                text=True
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except:
            return None
    
    def backup_current_version(self) -> bool:
        """Create backup of current version"""
        try:
            backup_dir = self.app_dir / "backups" / f"backup_{int(time.time())}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy critical files
            critical_files = ["api_server.py", "config/", "src/"]
            for file_path in critical_files:
                source = self.app_dir / file_path
                if source.exists():
                    if source.is_dir():
                        subprocess.run(["cp", "-r", str(source), str(backup_dir)], check=True)
                    else:
                        subprocess.run(["cp", str(source), str(backup_dir)], check=True)
            
            logger.info(f"✅ Backup created: {backup_dir}")
            return True
        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
            return False
    
    def update_code(self) -> bool:
        """Pull latest code from git"""
        try:
            # Pull latest changes
            result = subprocess.run(
                ["git", "pull", "origin", self.branch],
                cwd=self.app_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"❌ Git pull failed: {result.stderr}")
                return False
            
            # Update dependencies
            if (self.app_dir / "requirements.txt").exists():
                subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
                ], cwd=self.app_dir, check=True)
            
            logger.info("✅ Code updated successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Update failed: {e}")
            return False
    
    def restart_service(self) -> bool:
        """Restart the streaming service"""
        try:
            # Kill existing process
            subprocess.run(["pkill", "-f", "python.*api_server.py"], check=False)
            time.sleep(2)
            
            # Start new process
            subprocess.Popen([
                sys.executable, "api_server.py"
            ], cwd=self.app_dir)
            
            # Wait for service to start
            for _ in range(30):  # Wait up to 30 seconds
                time.sleep(1)
                if self.check_service_health():
                    logger.info("✅ Service restarted successfully")
                    return True
            
            logger.error("❌ Service failed to start after restart")
            return False
        except Exception as e:
            logger.error(f"❌ Restart failed: {e}")
            return False
    
    def perform_update(self) -> bool:
        """Perform complete update process"""
        logger.info("🔄 Starting update process...")
        
        # Check current status
        current_commit = self.get_current_commit()
        remote_commit = self.get_remote_commit()
        
        if not current_commit or not remote_commit:
            logger.error("❌ Unable to get commit information")
            return False
        
        if current_commit == remote_commit:
            logger.info("✅ Already up to date")
            return True
        
        logger.info(f"📥 Update available: {current_commit[:8]} -> {remote_commit[:8]}")
        
        # Backup current version
        if not self.backup_current_version():
            logger.error("❌ Backup failed, aborting update")
            return False
        
        # Update code
        if not self.update_code():
            logger.error("❌ Code update failed")
            return False
        
        # Restart service
        if not self.restart_service():
            logger.error("❌ Service restart failed")
            return False
        
        logger.info("🎉 Update completed successfully!")
        return True

def main():
    """Main update loop"""
    repo_url = os.getenv("GIT_REPO_URL", "")
    update_interval = int(os.getenv("UPDATE_INTERVAL", "300"))  # 5 minutes default
    
    if not repo_url:
        logger.error("❌ GIT_REPO_URL environment variable not set")
        sys.exit(1)
    
    updater = RemoteUpdater(repo_url)
    
    logger.info(f"🚀 Remote updater started (checking every {update_interval}s)")
    
    while True:
        try:
            updater.perform_update()
        except Exception as e:
            logger.error(f"❌ Update check failed: {e}")
        
        time.sleep(update_interval)

if __name__ == "__main__":
    main()
