#!/usr/bin/env python3

"""
Linux Setup Orchestrator for mcp-accurate-click-server

Detects Linux distribution and runs appropriate setup scripts and installation procedures.
Provides comprehensive system validation and compatibility checking.
"""

import argparse
import logging
import sys
import os
import subprocess
import stat
from pathlib import Path
from typing import Optional

# Add detection modules to path
SCRIPT_DIR = Path(__file__).parent
DETECTION_DIR = SCRIPT_DIR / 'detection'
SCRIPTS_DIR = SCRIPT_DIR / 'scripts'
MATRIX_DIR = SCRIPT_DIR / 'matrix'

if DETECTION_DIR not in sys.path:
    sys.path.insert(0, str(DETECTION_DIR))
if MATRIX_DIR not in sys.path:
    sys.path.insert(0, str(MATRIX_DIR))

from distro_detector import (
    DistributionDetector,
    PackageManager,
    DisplayServer,
    get_detector,
)
from tool_detector import ToolDetector, get_tool_detector
from compatibility_matrix import CompatibilityMatrix, DistroFamily

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SetupOrchestrator:
    """Orchestrates Linux setup for mcp-accurate-click-server."""

    def __init__(self, verbose: bool = False, dry_run: bool = False):
        """
        Initialize orchestrator.

        Args:
            verbose: Enable verbose logging
            dry_run: Show what would be done without making changes
        """
        self.verbose = verbose
        self.dry_run = dry_run
        self.detector = get_detector()
        self.tool_detector = get_tool_detector()
        self.distro_info = None
        self.distro_family = None

        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)

    def run(self) -> bool:
        """
        Run complete setup process.

        Returns:
            True if setup succeeded, False otherwise
        """
        print("\n" + "=" * 70)
        print("mcp-accurate-click-server - Linux Setup")
        print("=" * 70 + "\n")

        try:
            # Step 1: Detect distribution
            if not self._detect_distribution():
                return False

            # Step 2: Validate compatibility
            if not self._validate_compatibility():
                return False

            # Step 3: Detect tools
            if not self._detect_tools():
                return False

            # Step 4: Show summary
            self._show_summary()

            # Step 5: Run setup (if not dry run)
            if not self.dry_run:
                if not self._run_setup():
                    return False
            else:
                print("\n[DRY RUN] Setup commands would be executed here\n")

            # Step 6: Verify installation
            if not self.dry_run:
                if not self._verify_installation():
                    logger.warning("Verification had some issues, but setup may still work")

            return True

        except Exception as e:
            logger.error(f"Setup failed: {e}", exc_info=self.verbose)
            return False

    def _detect_distribution(self) -> bool:
        """Detect Linux distribution."""
        print("Step 1: Detecting Linux Distribution...")
        print("-" * 70)

        self.distro_info = self.detector.detect()

        print(f"  Distribution: {self.distro_info.distro_name} {self.distro_info.distro_version}")
        print(f"  Distribution ID: {self.distro_info.distro_id}")
        print(f"  Package Manager: {self.distro_info.package_manager.value}")
        print(f"  Desktop Environment: {self.distro_info.desktop_env.value}")
        print(f"  Display Server: {self.distro_info.display_server.value}")
        print(f"  Python Version: {self.distro_info.python_version}")

        if self.distro_info.is_wsl:
            print("  Note: Running in WSL (Windows Subsystem for Linux)")
        if self.distro_info.is_container:
            print("  Note: Running in container environment")

        print()

        return self.distro_info.package_manager != PackageManager.UNKNOWN

    def _validate_compatibility(self) -> bool:
        """Validate distribution compatibility."""
        print("Step 2: Validating Distribution Compatibility...")
        print("-" * 70)

        self.distro_family = CompatibilityMatrix.get_distro_family(
            self.distro_info.distro_id
        )

        if self.distro_family == DistroFamily.UNKNOWN:
            print(f"  WARNING: Distribution family not recognized")
            print(f"  Detected package manager: {self.distro_info.package_manager.value}")
            print(f"  May still work, but compatibility not guaranteed\n")
            return False

        print(f"  Distribution Family: {self.distro_family.value}")
        print(f"  Compatibility: OK\n")

        return True

    def _detect_tools(self) -> bool:
        """Detect available tools."""
        print("Step 3: Detecting Available Tools...")
        print("-" * 70)

        tools = self.tool_detector.detect_all()

        print("\nSystem Tools:")
        required_missing = []
        for name, tool in tools.items():
            status = tool.status.value
            version = f"({tool.version})" if tool.version else ""
            required = "[REQUIRED]" if tool.required else "[OPTIONAL]"

            if tool.status.value == "available":
                print(f"  ✓ {name:15} {status:20} {version:15} {required}")
            else:
                print(f"  ✗ {name:15} {status:20} {version:15} {required}")
                if tool.required:
                    required_missing.append(name)

        print("\nPython Modules:")
        python_modules = self.tool_detector.get_python_modules_status()
        for name, available in python_modules.items():
            if available:
                print(f"  ✓ {name:15} available")
            else:
                print(f"  ✗ {name:15} missing")

        print()

        return len(required_missing) == 0

    def _show_summary(self) -> None:
        """Show setup summary."""
        print("Step 4: Setup Summary...")
        print("-" * 70)

        print(f"\nDistribution: {self.distro_info.distro_name} {self.distro_info.distro_version}")
        print(f"Family: {self.distro_family.value}")
        print(f"Package Manager: {self.distro_info.package_manager.value}")

        print("\nPackages to install:")
        packages = CompatibilityMatrix.get_all_required_packages(self.distro_family)
        for pkg in packages:
            print(f"  - {pkg}")

        print()

    def _run_setup(self) -> bool:
        """Run distribution-specific setup script."""
        print("Step 5: Running Distribution-Specific Setup...")
        print("-" * 70 + "\n")

        # Map family to script
        script_map = {
            DistroFamily.DEBIAN: 'setup_ubuntu_debian.sh',
            DistroFamily.FEDORA: 'setup_fedora_rhel.sh',
            DistroFamily.ARCH: 'setup_arch.sh',
            DistroFamily.OPENSUSE: 'setup_opensuse.sh',
        }

        script_name = script_map.get(self.distro_family)
        if not script_name:
            logger.error(f"No setup script for {self.distro_family.value}")
            return False

        script_path = SCRIPTS_DIR / script_name
        if not script_path.exists():
            logger.error(f"Setup script not found: {script_path}")
            return False

        # Make script executable
        st = script_path.stat()
        script_path.chmod(st.st_mode | stat.S_IEXEC)

        # Run script
        try:
            result = subprocess.run(
                [str(script_path)],
                check=False
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to run setup script: {e}")
            return False

    def _verify_installation(self) -> bool:
        """Verify installation."""
        print("\nStep 6: Verifying Installation...")
        print("-" * 70)

        # Re-detect tools
        self.tool_detector._tools_cache.clear()
        self.tool_detector._python_modules.clear()

        print(self.tool_detector.get_summary())

        missing = self.tool_detector.get_missing_tools()
        if missing:
            logger.warning(f"Missing required tools: {', '.join(missing)}")
            return False

        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Setup mcp-accurate-click-server for Linux',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sudo python3 setup.py                    # Run full setup
  python3 setup.py --dry-run               # Show what would be done
  python3 setup.py --verbose               # Verbose output
  python3 setup.py --check-only            # Only check compatibility
        """
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '--check-only',
        action='store_true',
        help='Only check compatibility, do not install'
    )

    args = parser.parse_args()

    # Create orchestrator
    orchestrator = SetupOrchestrator(
        verbose=args.verbose,
        dry_run=args.dry_run or args.check_only
    )

    # Run setup
    success = orchestrator.run()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
