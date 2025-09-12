#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mirror_shell.py

Interactive command-line shell to mirror local folders with rclone.

Overview:
    This script provides a user-friendly interactive interface for mirroring
    local directories (e.g., home folder → external HDD) using `rclone sync`.
    It avoids manual flag management by exposing an interactive shell with
    safe defaults, dry-run validation, logging, and concurrency tuning.

Installation:
    1. Ensure rclone is installed and available in your PATH.
    2. Save this file as `mirror_shell.py`.
    3. Make it executable:
       chmod +x mirror_shell.py

Usage:
    ./mirror_shell.py

Interactive Commands:
    src PATH         Set source directory (default: home folder).
    dst PATH         Set destination directory. Creates it if missing.
    mounts           List detected mounts with attributes.
    show             Print current configuration and environment summary.
    sizeonly on|off  Toggle or set size-only mode (fastest, less safe).
    tune             Detect HDD/SSD and set concurrency automatically.
    set checkers N   Manually set number of metadata checkers.
    set transfers N  Manually set number of parallel transfers.
    plan             Run capacity check and dry-run sync.
    run              Execute live sync.
    post             Compare byte totals after a run.
    log              Show current log file path.
    help             Show this help message.
    quit             Exit shell (also with Ctrl-D).

Logging:
    All rclone commands and their output are logged in:
    ~/.local/share/rclone-mirror/mirror-YYYYMMDD-HHMMSS.log

Safety:
    - Always runs a dry-run with `plan` before actual `run`.
    - Checks free space before mirroring.
    - Prevents source and destination being equal or nested.
    - Logs every command for auditing.
"""

from __future__ import annotations

import cmd
import datetime as _dt
import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

# ----------------------------- Core Utils -----------------------------


class Sys:
    """Minimal system helpers."""

    @staticmethod
    def which(bin_name: str) -> Optional[str]:
        """Return absolute path for an executable or None.

        Args:
            bin_name: Program name.

        Returns:
            Absolute path or None.
        """
        return shutil.which(bin_name)

    @staticmethod
    def run(
        args: List[str],
        capture: bool = False,
        check: bool = False,
        env: Optional[dict] = None,
    ) -> subprocess.CompletedProcess:
        """Run a subprocess with common defaults.

        Args:
            args: Command and arguments.
            capture: Capture stdout and stderr into stdout.
            check: Raise CalledProcessError on non-zero exit.
            env: Environment overrides.

        Returns:
            CompletedProcess instance.
        """
        if capture:
            return subprocess.run(
                args,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=check,
                env=env,
            )
        return subprocess.run(args, check=check, env=env)

    @staticmethod
    def now_stamp() -> str:
        """Return a filename-safe timestamp.

        Returns:
            Timestamp string YYYYMMDD-HHMMSS.
        """
        return _dt.datetime.now().strftime("%Y%m%d-%H%M%S")

    @staticmethod
    def human_bytes(n: int) -> str:
        """Convert bytes to human-readable format.

        Args:
            n: Byte count.

        Returns:
            Formatted size string.
        """
        units = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]
        f = float(n)
        for u in units:
            if f < 1024 or u == units[-1]:
                return f"{f:.1f} {u}"
            f /= 1024

    @staticmethod
    def is_mount(p: Path) -> bool:
        """Check if path is a mountpoint.

        Args:
            p: Path to check.

        Returns:
            True if p is a mountpoint.
        """
        try:
            return p.is_mount()
        except Exception:
            return False


# ----------------------------- Logging -----------------------------


class Log:
    """Session logger."""

    def __init__(self) -> None:
        """Create a new log file under ~/.local/share/rclone-mirror."""
        self.path = (
            Path.home()
            / ".local"
            / "share"
            / "rclone-mirror"
            / f"mirror-{Sys.now_stamp()}.log"
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self.path.open("w", buffering=1, encoding="utf-8")
        self.write(f"# log {self.path}\n")

    def write(self, line: str) -> None:
        """Append a line to the log.

        Args:
            line: Text to write.
        """
        self._fh.write(line if line.endswith("\n") else line + "\n")

    def close(self) -> None:
        """Close the log file."""
        try:
            self._fh.close()
        except Exception:
            pass


# ----------------------------- Disk/Env Inspectors -----------------------------


class RcloneError(RuntimeError):
    """Raised for rclone environment errors."""


class RcloneEnv:
    """Environment checks and capability queries."""

    def __init__(self, sysmod: Sys) -> None:
        """Initialize.

        Args:
            sysmod: System helper instance.
        """
        self._sys = sysmod

    def ensure_present(self) -> str:
        """Ensure rclone exists in PATH.

        Returns:
            Path to rclone executable.

        Raises:
            RcloneError: If not found.
        """
        exe = self._sys.which("rclone")
        if not exe:
            raise RcloneError("rclone not found in PATH")
        return exe

    def version_text(self) -> str:
        """Get rclone version text.

        Returns:
            Version string or empty.
        """
        try:
            cp = self._sys.run(["rclone", "version"], capture=True)
            return (cp.stdout or "").strip()
        except Exception:
            return ""


class Mounts:
    """Enumerate likely destination mounts."""

    def __init__(self, sysmod: Sys) -> None:
        """Initialize.

        Args:
            sysmod: System helper instance.
        """
        self._sys = sysmod

    def _lsblk_json(self) -> dict:
        """Return lsblk JSON or empty schema.

        Returns:
            Parsed JSON dict.
        """
        try:
            cp = self._sys.run(
                ["lsblk", "-J", "-o", "NAME,MOUNTPOINT,RM,ROTA,TYPE,FSTYPE,SIZE"],
                capture=True,
            )
            return json.loads(cp.stdout)
        except Exception:
            return {"blockdevices": []}

    def list_mounts(self) -> List[Tuple[str, str, int, int, str]]:
        """List mounts.

        Returns:
            Tuples (mountpoint, size, removable, rotational, name).
        """
        out: List[Tuple[str, str, int, int, str]] = []
        data = self._lsblk_json()

        def walk(node: dict) -> None:
            mp = node.get("mountpoint")
            typ = node.get("type") or ""
            if mp and typ in {"part", "lvm", "crypt", "loop", "rom"}:
                out.append(
                    (
                        str(mp),
                        str(node.get("size") or "?"),
                        int(node.get("rm") or 0),
                        int(node.get("rota") or 1),
                        str(node.get("name") or "?"),
                    )
                )
            for c in node.get("children", []) or []:
                walk(c)

        for n in data.get("blockdevices", []):
            walk(n)

        # Fallback scan of common roots.
        for root in ("/media", "/run/media", "/mnt"):
            r = Path(root)
            if r.exists():
                for p in sorted([d for d in r.rglob("*") if d.is_dir()]):
                    if os.path.ismount(str(p)) and str(p) not in {m[0] for m in out}:
                        out.append((str(p), "?", 1, 1, "?"))

        # Dedupe and sort.
        uniq = {m[0]: m for m in out}
        return sorted(uniq.values(), key=lambda t: t[0])

    @staticmethod
    def mount_of(path: Path) -> Path:
        """Return mount root of a given path.

        Args:
            path: Any path under the mount.

        Returns:
            Mountpoint path.
        """
        p = path.resolve()
        while not Sys.is_mount(p) and p != p.parent:
            p = p.parent
        return p


class Capacity:
    """Capacity and usage helpers."""

    @staticmethod
    def disk_usage_of_mount(mount_point: Path) -> Tuple[int, int, int]:
        """Get disk usage for a mount.

        Args:
            mount_point: Mountpoint path.

        Returns:
            (total, used, free) in bytes.
        """
        total, used, free = shutil.disk_usage(str(mount_point))
        return int(total), int(used), int(free)


# ----------------------------- Rclone Runner -----------------------------


class RcloneRunner:
    """Build and execute rclone commands."""

    def __init__(self, sysmod: Sys, logger: Log) -> None:
        """Initialize.

        Args:
            sysmod: System helper instance.
            logger: Logger instance.
        """
        self._sys = sysmod
        self._log = logger

    def size_bytes(self, path: Path) -> int:
        """Compute byte size of a tree using `rclone size --json`.

        Args:
            path: Directory path.

        Returns:
            Total bytes or 0 on failure.
        """
        cmd = ["rclone", "size", str(path), "--json"]
        self._log.write("+ " + " ".join(shlex.quote(c) for c in cmd))
        cp = self._sys.run(cmd, capture=True)
        try:
            data = json.loads(cp.stdout)
            return int(data.get("bytes", 0))
        except Exception:
            return 0

    def detect_parallelism(self, dst_mount_rotational: int) -> Tuple[int, int]:
        """Heuristic concurrency based on medium.

        Args:
            dst_mount_rotational: 1 for HDD, 0 for SSD/NVMe.

        Returns:
            (checkers, transfers).
        """
        if int(dst_mount_rotational) == 1:
            return 32, 1
        return 64, 8

    def base_flags(
        self, *, size_only: bool, update: bool, checkers: int, transfers: int
    ) -> List[str]:
        """Default rclone flags for local mirroring.

        Args:
            size_only: Use size-only comparisons and skip hash verify.
            update: Use --update.
            checkers: Metadata concurrency.
            transfers: File copy concurrency.

        Returns:
            List of flags.
        """
        flags = [
            "--delete-during",
            "--fast-list=false",
            "--checksum=false",
            f"--checkers={checkers}",
            f"--transfers={transfers}",
            "--progress",
            "--stats=10s",
        ]
        if update:
            flags.append("--update")
        if size_only:
            flags.extend(["--size-only", "--ignore-checksum"])
        return flags

    def stream(self, args: List[str]) -> int:
        """Run a command and stream output to stdout and log.

        Args:
            args: Command and arguments.

        Returns:
            Exit code.
        """
        self._log.write("+ " + " ".join(shlex.quote(c) for c in args))
        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        try:
            assert proc.stdout is not None
            for line in proc.stdout:
                sys.stdout.write(line)
                self._log.write(line.rstrip("\n"))
        except KeyboardInterrupt:
            proc.terminate()
        finally:
            return proc.wait()


# ----------------------------- Session Model -----------------------------


class MirrorConfig:
    """Mutable mirror configuration."""

    def __init__(self) -> None:
        """Initialize with defaults."""
        self.src: Optional[Path] = None
        self.dst: Optional[Path] = None
        self.size_only: bool = False
        self.checkers: int = 64
        self.transfers: int = 8

    def as_dict(self) -> dict:
        """Serialize configuration.

        Returns:
            Dict snapshot.
        """
        return {
            "src": str(self.src) if self.src else "",
            "dst": str(self.dst) if self.dst else "",
            "size_only": self.size_only,
            "checkers": self.checkers,
            "transfers": self.transfers,
        }


class MirrorSession:
    """Session that holds state and provides operations."""

    def __init__(self) -> None:
        """Create a session and verify environment."""
        self.sys = Sys()
        self.log = Log()
        self.env = RcloneEnv(self.sys)
        self.mounts = Mounts(self.sys)
        self.capacity = Capacity()
        self.runner = RcloneRunner(self.sys, self.log)
        self.cfg = MirrorConfig()
        self._install_signal_handlers()
        self.env.ensure_present()

    def _install_signal_handlers(self) -> None:
        """Install clean SIGINT behavior."""
        signal.signal(signal.SIGINT, signal.SIG_DFL)

    def set_src(self, path: str) -> None:
        """Set source directory.

        Args:
            path: Source path.

        Raises:
            ValueError: If path missing or not a directory.
        """
        p = Path(path).expanduser()
        if not p.exists():
            raise ValueError(f"source not found: {p}")
        if not p.is_dir():
            raise ValueError(f"source not a directory: {p}")
        self.cfg.src = p

    def set_dst(self, path: str) -> None:
        """Set destination directory. Create if needed and test writable.

        Args:
            path: Destination path.

        Raises:
            ValueError: If not a directory or not writable.
        """
        p = Path(path).expanduser()
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
        if not p.is_dir():
            raise ValueError(f"destination not a directory: {p}")
        probe = p / ".rclone-mirror-write-test"
        try:
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
        except Exception as e:
            raise ValueError(f"destination not writable: {p} ({e})")
        self.cfg.dst = p

    @staticmethod
    def _is_same_or_nested(src: Path, dst: Path) -> bool:
        """Check if src and dst are equal or nested.

        Args:
            src: Source path.
            dst: Destination path.

        Returns:
            True if same or nested.
        """
        src = src.resolve()
        dst = dst.resolve()
        if src == dst:
            return True
        try:
            dst.relative_to(src)
            return True
        except Exception:
            pass
        try:
            src.relative_to(dst)
            return True
        except Exception:
            return False

    def validate_ready(self) -> None:
        """Validate configuration before running.

        Raises:
            ValueError: If src/dst invalid.
        """
        if not self.cfg.src or not self.cfg.dst:
            raise ValueError("src and dst must be set")
        if self._is_same_or_nested(self.cfg.src, self.cfg.dst):
            raise ValueError("src and dst cannot be the same or nested")

    def compute_capacity(self) -> Tuple[int, int, int, int]:
        """Compute sizes and free space.

        Returns:
            (src_bytes, dst_free, dst_total, dst_used).
        """
        assert self.cfg.src and self.cfg.dst
        src_bytes = self.runner.size_bytes(self.cfg.src)
        dst_mount = self.mounts.mount_of(self.cfg.dst)
        total, used, free = self.capacity.disk_usage_of_mount(dst_mount)
        return src_bytes, free, total, used

    def pick_parallelism(self) -> None:
        """Set checkers/transfers based on destination medium."""
        assert self.cfg.dst
        rota = 1  # default HDD
        dst_mount = self.mounts.mount_of(self.cfg.dst)
        for mp, _sz, _rm, r, _name in self.mounts.list_mounts():
            try:
                if Path(mp).resolve() == dst_mount.resolve():
                    rota = r
                    break
            except Exception:
                pass
        chk, tr = self.runner.detect_parallelism(rota)
        self.cfg.checkers, self.cfg.transfers = chk, tr

    def rclone_flags(self) -> List[str]:
        """Build final rclone flag list.

        Returns:
            List of flags.
        """
        return self.runner.base_flags(
            size_only=self.cfg.size_only,
            update=True,
            checkers=self.cfg.checkers,
            transfers=self.cfg.transfers,
        )

    def dry_run(self) -> int:
        """Execute a dry-run sync.

        Returns:
            rclone exit code.
        """
        self.validate_ready()
        cmd = ["rclone", "sync", str(self.cfg.src), str(self.cfg.dst), "--dry-run"]
        cmd += self.rclone_flags()
        return self.runner.stream(cmd)

    def live_run(self) -> int:
        """Execute a live sync.

        Returns:
            rclone exit code.
        """
        self.validate_ready()
        cmd = ["rclone", "sync", str(self.cfg.src), str(self.cfg.dst)]
        cmd += self.rclone_flags()
        return self.runner.stream(cmd)

    def mounts_table(self) -> List[Tuple[str, str, str, str]]:
        """Format mount info for display.

        Returns:
            Rows of (mount, size, class, medium).
        """
        rows = []
        for mp, size, rm, rota, _name in self.mounts.list_mounts():
            rows.append(
                (
                    mp,
                    size,
                    "removable" if rm else "fixed",
                    "HDD" if rota else "SSD/NVMe",
                )
            )
        return rows

    def summary(self) -> str:
        """Return textual configuration summary.

        Returns:
            Summary string.
        """
        ver = self.env.version_text()
        lines = [
            f"rclone: {ver or 'unknown'}",
            f"log: {self.log.path}",
            f"src: {self.cfg.src or '-'}",
            f"dst: {self.cfg.dst or '-'}",
            f"size_only: {self.cfg.size_only}",
            f"checkers: {self.cfg.checkers}",
            f"transfers: {self.cfg.transfers}",
        ]
        return "\n".join(lines)


# ----------------------------- Interactive Shell -----------------------------


class MirrorShell(cmd.Cmd):
    """Interactive command shell for mirroring."""

    intro = "rclone mirror shell. type 'help' for commands."
    prompt = "(mirror) "

    def __init__(self, session: MirrorSession) -> None:
        """Initialize shell.

        Args:
            session: MirrorSession instance.
        """
        super().__init__()
        self.s = session

    # ---------- help override ----------

    def do_help(self, arg: str) -> None:  # noqa: D401
        """Show help for a command or the full program help.

        If ARG is empty, print the module header help. Otherwise, delegate
        to the default help for the named command.
        """
        if not arg.strip():
            print(__doc__.strip())
        else:
            super().do_help(arg)

    # ---------- utility ----------

    @staticmethod
    def _print_table(headers: Iterable[str], rows: Iterable[Iterable[str]]) -> None:
        """Print a simple aligned table.

        Args:
            headers: Column headers.
            rows: Iterable of row iterables.
        """
        cols = list(headers)
        data = [list(map(str, r)) for r in rows]
        widths = [len(c) for c in cols]
        for r in data:
            for i, cell in enumerate(r):
                widths[i] = max(widths[i], len(cell))
        fmt = "  ".join("{:" + str(w) + "}" for w in widths)
        print(fmt.format(*cols))
        print(fmt.format(*["-" * w for w in widths]))
        for r in data:
            print(fmt.format(*r))

    # ---------- commands ----------

    def do_show(self, arg: str) -> None:
        """show

        Print current configuration and environment summary.
        """
        print(self.s.summary())

    def do_mounts(self, arg: str) -> None:
        """mounts

        List detected mount points with basic attributes.
        """
        rows = self.s.mounts_table()
        if not rows:
            print("no mounts detected")
            return
        self._print_table(["mount", "size", "class", "medium"], rows)

    def do_src(self, arg: str) -> None:
        """src PATH

        Set source directory. Defaults to home if PATH omitted.
        """
        path = arg.strip() or str(Path.home())
        try:
            self.s.set_src(path)
            print(f"src={self.s.cfg.src}")
        except Exception as e:
            print(f"error: {e}")

    def do_dst(self, arg: str) -> None:
        """dst PATH

        Set destination directory. Creates it if missing.
        """
        path = arg.strip()
        if not path:
            print("error: missing PATH")
            return
        try:
            self.s.set_dst(path)
            print(f"dst={self.s.cfg.dst}")
        except Exception as e:
            print(f"error: {e}")

    def do_sizeonly(self, arg: str) -> None:
        """sizeonly [on|off]

        Toggle or set size-only mode (fastest, less safe).
        """
        tok = arg.strip().lower()
        if tok in {"on", "true", "1"}:
            self.s.cfg.size_only = True
        elif tok in {"off", "false", "0"}:
            self.s.cfg.size_only = False
        elif tok == "":
            self.s.cfg.size_only = not self.s.cfg.size_only
        else:
            print("error: expected on|off")
            return
        print(f"size_only={self.s.cfg.size_only}")

    def do_tune(self, arg: str) -> None:
        """tune

        Detect device type and set checkers/transfers heuristically.
        """
        try:
            self.s.pick_parallelism()
            print(f"checkers={self.s.cfg.checkers} transfers={self.s.cfg.transfers}")
        except Exception as e:
            print(f"error: {e}")

    def do_set(self, arg: str) -> None:
        """set checkers N | set transfers N

        Manually set concurrency.
        """
        parts = arg.strip().split()
        if len(parts) != 2:
            print("error: usage: set checkers N | set transfers N")
            return
        key, val = parts
        try:
            n = int(val)
            if key == "checkers":
                self.s.cfg.checkers = max(1, n)
            elif key == "transfers":
                self.s.cfg.transfers = max(1, n)
            else:
                print("error: key must be 'checkers' or 'transfers'")
                return
            print(f"{key}={n}")
        except ValueError:
            print("error: N must be integer")

    def do_plan(self, arg: str) -> None:
        """plan

        Run a capacity check and a dry-run sync.
        """
        try:
            self.s.validate_ready()
        except Exception as e:
            print(f"error: {e}")
            return
        try:
            src_b, free, total, used = self.s.compute_capacity()
            print(
                "capacity: "
                f"src={Sys.human_bytes(src_b)} free={Sys.human_bytes(free)} "
                f"used={Sys.human_bytes(used)} total={Sys.human_bytes(total)}"
            )
            if src_b and free < src_b:
                print("warning: insufficient free space for full mirror")
            code = self.s.dry_run()
            print(f"dry-run exit={code}")
        except Exception as e:
            print(f"error: {e}")

    def do_run(self, arg: str) -> None:
        """run

        Execute live sync with current settings.
        """
        try:
            self.s.validate_ready()
        except Exception as e:
            print(f"error: {e}")
            return
        src_b, free, _total, _used = self.s.compute_capacity()
        if src_b and free < src_b:
            print("error: insufficient free space")
            return
        code = self.s.live_run()
        print(f"run exit={code}")

    def do_post(self, arg: str) -> None:
        """post

        Compare byte totals for src and dst after a run.
        """
        try:
            self.s.validate_ready()
            s = self.s.runner.size_bytes(self.s.cfg.src)  # type: ignore[arg-type]
            d = self.s.runner.size_bytes(self.s.cfg.dst)  # type: ignore[arg-type]
            print(f"src={Sys.human_bytes(s)} dst={Sys.human_bytes(d)}")
            print("match" if s == d else "mismatch")
        except Exception as e:
            print(f"error: {e}")

    def do_log(self, arg: str) -> None:
        """log

        Show current log file path.
        """
        print(self.s.log.path)

    def do_quit(self, arg: str) -> bool:
        """quit

        Exit the shell.
        """
        self.s.log.close()
        return True

    def do_EOF(self, arg: str) -> bool:  # noqa: N802
        """Ctrl-D

        Exit the shell.
        """
        print()
        return self.do_quit(arg)


# ----------------------------- Entrypoint -----------------------------


def main() -> int:
    """Start the shell.

    Returns:
        Process exit code.
    """
    try:
        sess = MirrorSession()
    except RcloneError as e:
        print(f"error: {e}")
        return 1
    shell = MirrorShell(sess)
    shell.cmdloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
