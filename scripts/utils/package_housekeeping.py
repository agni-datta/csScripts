#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""package_housekeeping.py

Backup and restore utility for DNF packages (on Fedora) and Flatpak applications.

DNF (Fedora only):
  - Backup: `dnf repoquery --qf "%{name}" --userinstalled` → $HOME/.config/fedora/fedora_installed.conf
  - Restore: read that file and run `sudo dnf install -y <packages>`

Flatpak:
  - Backup: `flatpak list --columns=application --app` → $HOME/.config/flatpak/flatpaks_installed.conf
  - Restore: read that file and run `xargs -a flatpaks_installed.conf flatpak install -y`

Logs:
  - Each run writes $HOME/.config/fedora/backup-<HHSS>-<DDMMYYYY>.log
  - Menu option prints the last 50 lines of the newest log with color
"""

from __future__ import annotations

import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class Rgb:
    """RGB triplet.

    Attributes:
        r: Red component.
        g: Green component.
        b: Blue component.
    """

    r: int
    g: int
    b: int


@dataclass(frozen=True)
class CatppuccinMochaPalette:
    """Catppuccin Mocha base palette."""

    text: Rgb = Rgb(205, 214, 244)
    subtext0: Rgb = Rgb(166, 173, 200)
    overlay0: Rgb = Rgb(108, 112, 134)
    red: Rgb = Rgb(243, 139, 168)
    yellow: Rgb = Rgb(249, 226, 175)
    green: Rgb = Rgb(166, 227, 161)
    blue: Rgb = Rgb(137, 180, 250)
    mauve: Rgb = Rgb(203, 166, 247)
    peach: Rgb = Rgb(250, 179, 135)
    sky: Rgb = Rgb(137, 220, 235)


class AnsiStyler:
    """ANSI styling with Catppuccin Mocha palette."""

    _RESET: str = "\033[0m"

    def __init__(self, palette: CatppuccinMochaPalette) -> None:
        """Initialize styler with palette."""
        self._palette = palette
        self._enabled = sys.stdout.isatty()

    @staticmethod
    def _fg(rgb: Rgb) -> str:
        """Return ANSI escape sequence for foreground color."""
        return f"\033[38;2;{rgb.r};{rgb.g};{rgb.b}m"

    def colorize(self, text: str, rgb: Rgb) -> str:
        """Colorize text if stdout is a TTY."""
        if not self._enabled:
            return text
        return f"{self._fg(rgb)}{text}{self._RESET}"

    def bold(self, text: str) -> str:
        """Return bold text if stdout is a TTY."""
        if not self._enabled:
            return text
        return f"\033[1m{text}{self._RESET}"


class SystemInfo:
    """System detection utilities."""

    @staticmethod
    def is_fedora() -> bool:
        """Return True if host is Fedora-based."""
        try:
            data = Path("/etc/os-release").read_text(encoding="utf-8")
        except OSError:
            return False
        fields: Dict[str, str] = {}
        for line in data.splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                fields[k.strip()] = v.strip().strip('"').lower()
        os_id = fields.get("ID", "")
        os_like = fields.get("ID_LIKE", "")
        return os_id == "fedora" or "fedora" in os_like


@dataclass(frozen=True)
class PathConfig:
    """Configuration for filesystem paths used by the app."""

    home_dir: Path = Path.home()
    fedora_dir: Path = Path.home() / ".config" / "fedora"
    flatpak_dir: Path = Path.home() / ".config" / "flatpak"
    dnf_backup_file: Path = Path.home() / ".config" / "fedora" / "fedora_installed.conf"
    flatpak_backup_file: Path = (
        Path.home() / ".config" / "flatpak" / "flatpaks_installed.conf"
    )

    def ensure_dirs(self) -> None:
        """Create config directories if missing."""
        self.fedora_dir.mkdir(parents=True, exist_ok=True)
        self.flatpak_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def log_filename() -> str:
        """Return timestamped log filename."""
        stamp = datetime.now().strftime("%H%S-%d%m%Y")
        return f"backup-{stamp}.log"


class ProcessRunner:
    """Subprocess utilities."""

    @staticmethod
    def run(argv: Sequence[str]) -> Tuple[int, str, str]:
        """Run subprocess and capture stdout, stderr."""
        proc = subprocess.run(
            list(argv),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        return proc.returncode, proc.stdout, proc.stderr

    @staticmethod
    def ensure_tool(name: str) -> None:
        """Raise if tool is missing from PATH."""
        if shutil.which(name) is None:
            raise RuntimeError(f"Required executable not found: {name}")

    @staticmethod
    def read_nonempty_lines(path: Path) -> List[str]:
        """Read file and return nonempty, noncomment lines."""
        out: List[str] = []
        with path.open("r", encoding="utf-8") as handle:
            for raw in handle:
                s = raw.strip()
                if not s or s.startswith("#"):
                    continue
                out.append(s)
        return out


class LogLevel(Enum):
    """Logging severity levels."""

    INFO = "INFO"
    OK = "OK"
    WARN = "WARN"
    ERROR = "ERROR"
    STDOUT = "STDOUT"
    STDERR = "STDERR"


class RunLogger:
    """Logger for each run, with console colors and file sink."""

    def __init__(self, paths: PathConfig, styler: AnsiStyler) -> None:
        self._paths = paths
        self._styler = styler
        self._paths.ensure_dirs()
        self._log_path = self._paths.fedora_dir / self._paths.log_filename()
        self._log_path.write_text("", encoding="utf-8")

    def _color_for(self, level: LogLevel) -> Rgb:
        """Return palette color for log level."""
        p = self._styler._palette
        return {
            LogLevel.INFO: p.sky,
            LogLevel.OK: p.green,
            LogLevel.WARN: p.peach,
            LogLevel.ERROR: p.red,
            LogLevel.STDERR: p.red,
            LogLevel.STDOUT: p.overlay0,
        }[level]

    def write_line(self, line: str) -> None:
        """Write line to log file."""
        with self._log_path.open("a", encoding="utf-8") as handle:
            handle.write(line.rstrip() + "\n")

    def log(self, level: LogLevel, message: str) -> None:
        """Log message with severity."""
        txt = f"{level.value}: {message}"
        print(self._styler.colorize(txt, self._color_for(level)))
        self.write_line(txt)

    def tail_latest(self, max_lines: int = 50) -> Optional[List[str]]:
        """Return last lines of most recent log file."""
        logs = sorted(self._paths.fedora_dir.glob("backup-*-*.log"))
        if not logs:
            return None
        latest = logs[-1]
        try:
            data = latest.read_text(encoding="utf-8").splitlines()
            return data[-max_lines:]
        except OSError:
            return None


class DnfService:
    """DNF backup and restore service."""

    def __init__(self, paths: PathConfig, logger: RunLogger) -> None:
        self._paths = paths
        self._logger = logger

    def _ensure_tools(self) -> None:
        """Ensure dnf is installed."""
        ProcessRunner.ensure_tool("dnf")

    def backup(self) -> None:
        """Backup user-installed DNF packages."""
        self._ensure_tools()
        self._paths.ensure_dirs()
        out_path = self._paths.dnf_backup_file
        if out_path.exists():
            self._logger.log(LogLevel.WARN, f"Removing old backup: {out_path}")
            out_path.unlink()
        rc, out, err = ProcessRunner.run(
            ["dnf", "repoquery", "--qf", "%{name}\\n", "--userinstalled"]
        )
        if rc != 0:
            if err:
                self._logger.log(LogLevel.ERROR, err.strip())
            raise RuntimeError("dnf repoquery failed")
        pkgs = [line for line in (s.strip() for s in out.splitlines()) if line]
        out_path.write_text("\n".join(pkgs) + "\n", encoding="utf-8")
        self._logger.log(
            LogLevel.OK, f"DNF backup written: {out_path} ({len(pkgs)} packages)"
        )

    def install(self) -> None:
        """Install packages from backup file."""
        self._ensure_tools()
        in_path = self._paths.dnf_backup_file
        if not in_path.exists():
            raise FileNotFoundError(f"Missing DNF backup: {in_path}")
        raw = in_path.read_text(encoding="utf-8")
        pkgs = [p for p in raw.replace("\t", " ").split() if p]
        if not pkgs:
            self._logger.log(LogLevel.WARN, "DNF list is empty. Nothing to install.")
            return
        argv = ["sudo", "dnf", "install", "-y", *pkgs]
        self._logger.log(LogLevel.INFO, f"Running: {shlex.join(argv)}")
        rc, out, err = ProcessRunner.run(argv)
        if out:
            for line in out.rstrip().splitlines():
                self._logger.log(LogLevel.STDOUT, line)
        if err:
            for line in err.rstrip().splitlines():
                self._logger.log(LogLevel.STDERR, line)
        if rc != 0:
            raise RuntimeError(
                f"Command failed with exit code {rc}: {shlex.join(argv)}"
            )
        self._logger.log(LogLevel.OK, f"DNF install completed for {len(pkgs)} packages")


class FlatpakService:
    """Flatpak backup and restore service."""

    def __init__(self, paths: PathConfig, logger: RunLogger) -> None:
        self._paths = paths
        self._logger = logger

    def _ensure_tools(self) -> None:
        """Ensure flatpak and xargs exist."""
        ProcessRunner.ensure_tool("flatpak")
        ProcessRunner.ensure_tool("xargs")

    def backup(self) -> None:
        """Backup installed Flatpak applications."""
        self._ensure_tools()
        self._paths.ensure_dirs()
        out_path = self._paths.flatpak_backup_file
        if out_path.exists():
            self._logger.log(LogLevel.WARN, f"Removing old backup: {out_path}")
            out_path.unlink()
        rc, out, err = ProcessRunner.run(
            ["flatpak", "list", "--columns=application", "--app"]
        )
        if rc != 0:
            if err:
                self._logger.log(LogLevel.ERROR, err.strip())
            raise RuntimeError("flatpak list failed")
        apps = [line for line in (s.strip() for s in out.splitlines()) if line]
        out_path.write_text("\n".join(apps) + "\n", encoding="utf-8")
        self._logger.log(
            LogLevel.OK, f"Flatpak backup written: {out_path} ({len(apps)} apps)"
        )

    def install(self) -> None:
        """Install Flatpak apps from backup file."""
        self._ensure_tools()
        in_path = self._paths.flatpak_backup_file
        if not in_path.exists():
            raise FileNotFoundError(f"Missing Flatpak backup: {in_path}")
        argv = [
            "bash",
            "-c",
            f"xargs -a {shlex.quote(str(in_path))} flatpak install -y",
        ]
        self._logger.log(LogLevel.INFO, f"Running: {shlex.join(argv)}")
        rc, out, err = ProcessRunner.run(argv)
        if out:
            for line in out.rstrip().splitlines():
                self._logger.log(LogLevel.STDOUT, line)
        if err:
            for line in err.rstrip().splitlines():
                self._logger.log(LogLevel.STDERR, line)
        if rc != 0:
            raise RuntimeError(
                f"Command failed with exit code {rc}: {shlex.join(argv)}"
            )
        self._logger.log(LogLevel.OK, "Flatpak install completed")


class HelpView:
    """Help renderer."""

    def __init__(self, styler: AnsiStyler) -> None:
        self._styler = styler

    def render(self) -> None:
        """Render manpage-style help."""
        bold = self._styler.bold
        print(bold("NAME"))
        print(
            "    package_housekeeping - backup and restore DNF and Flatpak packages\n"
        )
        print(bold("SYNOPSIS"))
        print("    package_housekeeping.py [OPTIONS]\n")
        print(bold("DESCRIPTION"))
        print(
            "    Provides backup and restore for Fedora DNF packages and Flatpak applications."
        )
        print(
            "    Backup files are stored under $HOME/.config/fedora and $HOME/.config/flatpak."
        )
        print("    Logs are stored in $HOME/.config/fedora.\n")
        print(bold("OPTIONS"))
        print("    1    Install from Fedora backup (DNF)")
        print("    2    Backup Fedora packages (DNF)")
        print("    3    Install from Flatpak backup")
        print("    4    Backup Flatpak applications")
        print("    5    Show latest log")
        print("    6    Help screen")
        print()


class MenuController:
    """Interactive menu controller."""

    def __init__(
        self,
        dnf: Optional[DnfService],
        flatpak: Optional[FlatpakService],
        logger: RunLogger,
        styler: AnsiStyler,
    ) -> None:
        self._dnf = dnf
        self._flatpak = flatpak
        self._logger = logger
        self._styler = styler

    def run_once(self) -> None:
        """Run one menu interaction."""
        options: Dict[str, Tuple[str, callable]] = {}
        if self._dnf and SystemInfo.is_fedora():
            options["1"] = ("Install from Fedora backup (DNF)", self._dnf.install)
            options["2"] = ("Backup Fedora packages (DNF)", self._dnf.backup)
        if self._flatpak:
            options["3"] = ("Install from Flatpak backup", self._flatpak.install)
            options["4"] = ("Backup Flatpak applications", self._flatpak.backup)
        options["5"] = ("Show latest log", self.show_log)
        options["6"] = ("Help screen", self.show_help)

        print(self._styler.bold("Select an option:"))
        for key, (desc, _) in options.items():
            print(f" {key}. {desc}")
        choice = input("> ").strip()
        if choice not in options:
            self._logger.log(LogLevel.ERROR, f"Invalid choice: {choice}")
            return
        _, action = options[choice]
        action()

    def show_log(self) -> None:
        """Display latest log tail with colors."""
        lines = self._logger.tail_latest()
        if lines is None:
            self._logger.log(LogLevel.WARN, "No log files found.")
            return
        for line in lines:
            if line.startswith("ERROR:"):
                print(self._styler.colorize(line, self._styler._palette.red))
            elif line.startswith("WARN:"):
                print(self._styler.colorize(line, self._styler._palette.peach))
            elif line.startswith("OK:"):
                print(self._styler.colorize(line, self._styler._palette.green))
            elif line.startswith("INFO:"):
                print(self._styler.colorize(line, self._styler._palette.sky))
            elif line.startswith("STDERR:"):
                print(self._styler.colorize(line, self._styler._palette.red))
            elif line.startswith("STDOUT:"):
                print(self._styler.colorize(line, self._styler._palette.overlay0))
            else:
                print(line)

    def show_help(self) -> None:
        """Render help view."""
        HelpView(self._styler).render()


class Application:
    """Main application class."""

    def __init__(self) -> None:
        palette = CatppuccinMochaPalette()
        self._styler = AnsiStyler(palette)
        self._paths = PathConfig()
        self._logger = RunLogger(self._paths, self._styler)
        self._dnf: Optional[DnfService] = None
        self._flatpak: Optional[FlatpakService] = None
        if SystemInfo.is_fedora():
            try:
                self._dnf = DnfService(self._paths, self._logger)
            except RuntimeError as e:
                self._logger.log(LogLevel.WARN, f"DNF unavailable: {e}")
        try:
            self._flatpak = FlatpakService(self._paths, self._logger)
        except RuntimeError as e:
            self._logger.log(LogLevel.WARN, f"Flatpak unavailable: {e}")

    def run(self) -> None:
        """Run the application once."""
        HelpView(self._styler).render()
        MenuController(self._dnf, self._flatpak, self._logger, self._styler).run_once()


def main() -> None:
    """Program entry point."""
    app = Application()
    try:
        app.run()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
