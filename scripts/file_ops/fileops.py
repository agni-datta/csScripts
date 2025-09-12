#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FileOps: Interactive and CLI file utility for Linux and macOS.

Overview:
    FileOps provides a modular, object-oriented toolkit for common filesystem
    workflows with optional integrations for modern command-line tools. The
    application supports interactive and non-interactive modes and logs all
    activity to a designated directory.

Key Features:
    * Directory listing using `eza` when available, otherwise a Python fallback.
    * Fuzzy selection using `fzf` when available, otherwise a minimal fallback.
    * Copy and move operations with a TTY progress bar. Recursive or not. Overwrite control.
    * Single and batch rename, with optional glob filtering and dry-run preview.
    * Mirroring using `rclone` (sync or copy semantics), with recursive, dry-run, and extra flags.
    * Optional path discovery using `zoxide`.
    * Structured, rotating file logs stored in a "money" directory or $MONEY_DIR.

Design:
    The code is organized into small classes that each implement one concern:
    logging, path listing, fuzzy selection, copying/moving, renaming, and
    mirroring. The `FileOpsApp` composes these services and exposes an
    interactive menu as well as subcommands.

Conventions:
    * Google-style docstrings and naming conventions.
    * Black-compatible formatting.
    * No mid-line comments; docstrings document behavior and parameters.
    * Standard library only for Python dependencies; optional external tools:
      eza, fzf, rclone, zoxide.

Logging:
    Logs are written to $MONEY_DIR/fileops.log or ~/money/fileops.log with
    rotation (5 MB per file, 5 backups) and include timestamps, levels,
    logger names, function names, line numbers, and messages.

Usage:
    Interactive:
        $ fileops

    Non-interactive:
        $ fileops list PATH [--no-all] [--no-long]
        $ fileops copy DEST SRC... [-r] [-f]
        $ fileops move DEST SRC... [-r] [-f]
        $ fileops mirror SRC DST [-r] [--no-delete-extra] [--dry-run] [--extra ...]
        $ fileops rename PATH... --replace NAME_OR_SUBST [--find SUBSTR] [--glob PATTERN] [--dry-run] [--batch]

Environment:
    MONEY_DIR: Optional directory path for logs. Defaults to ~/money.

"""

from __future__ import annotations

import argparse
import dataclasses
import fnmatch
import logging
import os
import shutil
import sys
import textwrap
from logging.handlers import RotatingFileHandler
from pathlib import Path
from subprocess import PIPE, CalledProcessError, Popen, run
from typing import Iterable, Iterator, List, Optional, Sequence, Tuple


def _ensure_log_dir() -> Path:
    """Ensure the log directory exists.

    Returns:
        Path: Absolute path to the log directory. Uses $MONEY_DIR, otherwise ~/money.
    """
    base = os.environ.get("MONEY_DIR", str(Path.home() / "money"))
    path = Path(base).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _setup_logger(name: str = "fileops", level: int = logging.INFO) -> logging.Logger:
    """Create a rotating logger configuration.

    Args:
        name: Logger name.
        level: Logging level.

    Returns:
        logging.Logger: Configured logger.
    """
    log_dir = _ensure_log_dir()
    log_file = log_dir / f"{name}.log"
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
    )
    fh = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=5)
    fh.setLevel(level)
    fh.setFormatter(fmt)
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(fmt)
    if not logger.handlers:
        logger.addHandler(fh)
        logger.addHandler(ch)
    return logger


LOG = _setup_logger()


def _which(cmd: str) -> Optional[str]:
    """Locate a command in PATH.

    Args:
        cmd: Command name.

    Returns:
        Optional[str]: Absolute path if found, else None.
    """
    return shutil.which(cmd)


def _human_size(n: int) -> str:
    """Convert bytes to a human-readable size string.

    Args:
        n: Byte count.

    Returns:
        str: Human-readable size with unit suffix.
    """
    units = ["B", "KB", "MB", "GB", "TB", "PB", "EB"]
    s = float(n)
    for u in units:
        if s < 1024.0:
            return f"{s:3.1f} {u}"
        s /= 1024.0
    return f"{s:.1f} ZB"


def _iter_paths(root: Path, recursive: bool) -> Iterator[Path]:
    """Iterate over entries under a root.

    Args:
        root: Root path to iterate.
        recursive: Whether to traverse recursively.

    Yields:
        Path: Child path.
    """
    if recursive:
        yield from root.rglob("*")
    else:
        yield from root.iterdir()


def _confirm_exists(path: Path) -> None:
    """Validate that a path exists.

    Args:
        path: Path to test.

    Raises:
        FileNotFoundError: If the path does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Path not found: {path}")


def _safe_input(prompt: str) -> str:
    """Read input and log the prompt and response.

    Args:
        prompt: Input prompt.

    Returns:
        str: User input stripped of surrounding whitespace.
    """
    s = input(prompt)
    LOG.info("INPUT %s -> %s", prompt, s)
    return s.strip()


def _run_cmd(cmd: Sequence[str], check: bool = True) -> Tuple[int, str, str]:
    """Execute a subprocess.

    Args:
        cmd: Command and arguments.
        check: Raise on nonzero exit if True.

    Returns:
        Tuple[int, str, str]: Return code, stdout, stderr.

    Raises:
        CalledProcessError: If check is True and the command fails.
    """
    LOG.info("RUN %s", " ".join(cmd))
    try:
        res = run(cmd, stdout=PIPE, stderr=PIPE, text=True, check=check)
        return res.returncode, res.stdout, res.stderr
    except CalledProcessError as exc:
        LOG.error("CMD FAILED %s | rc=%s | stderr=%s", cmd, exc.returncode, exc.stderr)
        if check:
            raise
        return exc.returncode, exc.stdout or "", exc.stderr or ""


@dataclasses.dataclass
class ToolRegistry:
    """Registry of external tools and their locations."""

    eza: Optional[str] = dataclasses.field(default_factory=lambda: _which("eza"))
    fzf: Optional[str] = dataclasses.field(default_factory=lambda: _which("fzf"))
    rclone: Optional[str] = dataclasses.field(default_factory=lambda: _which("rclone"))
    zoxide: Optional[str] = dataclasses.field(default_factory=lambda: _which("zoxide"))


class DirectoryLister:
    """Directory listing with optional `eza` integration."""

    def __init__(self, tools: ToolRegistry):
        """Initialize the lister.

        Args:
            tools: Tool registry with optional tool paths.
        """
        self._tools = tools

    def list(
        self, path: Path, include_all: bool = True, long_format: bool = True
    ) -> str:
        """Return a textual listing of a directory.

        Args:
            path: Directory to list.
            include_all: Include dotfiles if True.
            long_format: Use long listing format if True.

        Returns:
            str: Listing text.

        Raises:
            NotADirectoryError: If path is not a directory.
        """
        _confirm_exists(path)
        if not path.is_dir():
            raise NotADirectoryError(str(path))
        if self._tools.eza:
            cmd: List[str] = [self._tools.eza]
            if include_all:
                cmd.append("-a")
            if long_format:
                cmd.append("-l")
            cmd.append(str(path))
            _, out, _ = _run_cmd(cmd)
            return out
        entries = sorted(os.listdir(path))
        lines: List[str] = []
        for name in entries:
            if not include_all and name.startswith("."):
                continue
            p = path / name
            t = "d" if p.is_dir() else "-"
            size = _human_size(p.stat().st_size) if p.is_file() else ""
            lines.append(f"{t} {size:>8} {name}")
        return "\n".join(lines)


class FuzzySelector:
    """Fuzzy selection using `fzf` with a minimal fallback."""

    def __init__(self, tools: ToolRegistry):
        """Initialize the selector.

        Args:
            tools: Tool registry with optional tool paths.
        """
        self._tools = tools

    def choose(self, candidates: Iterable[str], multi: bool = False) -> List[str]:
        """Choose items with a fuzzy interface.

        Args:
            candidates: Items to select from.
            multi: Allow multiple selections.

        Returns:
            List[str]: Selected items in display order.
        """
        items = list(dict.fromkeys(candidates))
        if not items:
            return []
        if self._tools.fzf:
            fzf_cmd: List[str] = [self._tools.fzf]
            if multi:
                fzf_cmd.append("--multi")
            proc = Popen(fzf_cmd, stdin=PIPE, stdout=PIPE, text=True)
            assert proc.stdin is not None
            proc.stdin.write("\n".join(items))
            proc.stdin.close()
            out = proc.stdout.read() if proc.stdout else ""
            proc.wait()
            selected = [line.strip() for line in out.splitlines() if line.strip()]
            LOG.info("FZF selected %s", selected)
            return selected
        query = _safe_input("Query: ").lower()
        scored = [(s, s.lower().find(query)) for s in items]
        scored = [t for t in scored if t[1] >= 0]
        scored.sort(key=lambda x: x[1])
        if not scored:
            return []
        if multi:
            k = _safe_input("Max results: ")
            try:
                n = int(k or "5")
            except ValueError:
                n = 5
            return [s for s, _ in scored[:n]]
        return [scored[0][0]]


class ZoxideClient:
    """Query helper for `zoxide`."""

    def __init__(self, tools: ToolRegistry):
        """Initialize the client.

        Args:
            tools: Tool registry with optional tool paths.
        """
        self._tools = tools

    def query(self, pattern: str) -> List[str]:
        """Query zoxide for matching paths.

        Args:
            pattern: Query pattern passed to `zoxide query -l`.

        Returns:
            List[str]: Matching paths, or an empty list if unavailable.
        """
        if not self._tools.zoxide:
            return []
        rc, out, _ = _run_cmd([self._tools.zoxide, "query", "-l", pattern], check=False)
        if rc != 0:
            return []
        return [line.strip() for line in out.splitlines() if line.strip()]


class FileTransfer:
    """Copy and move operations with progress output."""

    def __init__(self, logger: logging.Logger):
        """Initialize the transfer service.

        Args:
            logger: Logger for operational messages.
        """
        self._log = logger

    def copy(
        self,
        sources: Sequence[Path],
        destination: Path,
        recursive: bool = True,
        overwrite: bool = False,
    ) -> None:
        """Copy files and directories with progress.

        Args:
            sources: Source paths.
            destination: Destination directory or file.
            recursive: Copy directory trees if True.
            overwrite: Overwrite existing files if True.
        """
        dest = destination.expanduser().resolve()
        dest.mkdir(parents=True, exist_ok=True)
        for src in sources:
            s = src.expanduser().resolve()
            _confirm_exists(s)
            if s.is_dir():
                if not recursive:
                    self._log.info("Skip directory without recursive: %s", s)
                    continue
                for path in s.rglob("*"):
                    if path.is_dir():
                        continue
                    rel = path.relative_to(s)
                    d = dest / s.name / rel
                    if d.exists() and not overwrite:
                        self._log.info("Skip existing: %s", d)
                        continue
                    self._copy_file(path, d)
            else:
                d = dest / s.name if dest.is_dir() else dest
                if d.exists() and not overwrite:
                    self._log.info("Skip existing: %s", d)
                    continue
                self._copy_file(s, d)

    def move(
        self,
        sources: Sequence[Path],
        destination: Path,
        recursive: bool = True,
        overwrite: bool = False,
    ) -> None:
        """Move files and directories with progress.

        Args:
            sources: Source paths.
            destination: Destination directory or file.
            recursive: Move directory trees if True.
            overwrite: Overwrite existing files if True.
        """
        self.copy(sources, destination, recursive=recursive, overwrite=overwrite)
        for src in sources:
            s = src.expanduser().resolve()
            if s.is_dir():
                shutil.rmtree(s)
            else:
                try:
                    s.unlink()
                except FileNotFoundError:
                    pass

    def _copy_file(self, src: Path, dst: Path, bufsize: int = 2 * 1024 * 1024) -> None:
        """Copy one file with a TTY progress bar.

        Args:
            src: Source file.
            dst: Destination file.
            bufsize: Read buffer size in bytes.

        Raises:
            OSError: On I/O failure.
        """
        total = src.stat().st_size
        done = 0
        dst.parent.mkdir(parents=True, exist_ok=True)
        with src.open("rb") as r, dst.open("wb") as w:
            while True:
                b = r.read(bufsize)
                if not b:
                    break
                w.write(b)
                done += len(b)
                self._print_progress(done, total, prefix=f"Copy {src.name}")
        print("")

    def _print_progress(self, done: int, total: int, prefix: str = "") -> None:
        """Render a single-line progress bar.

        Args:
            done: Bytes copied so far.
            total: Total bytes to copy.
            prefix: Progress label prefix.
        """
        width = 40
        ratio = 0 if total == 0 else min(1.0, done / total)
        filled = int(width * ratio)
        bar = "#" * filled + "-" * (width - filled)
        pct = f"{ratio * 100:5.1f}%"
        sys.stdout.write(
            f"\r{prefix:20} [{bar}] {pct} {_human_size(done)}/{_human_size(total)}"
        )
        sys.stdout.flush()


class RenameService:
    """Single and batch rename utilities."""

    def rename(self, target: Path, new_name: str) -> Path:
        """Rename a single path.

        Args:
            target: Path to rename.
            new_name: New basename for the target.

        Returns:
            Path: New absolute path.
        """
        t = target.expanduser().resolve()
        _confirm_exists(t)
        new_path = t.with_name(new_name)
        t.rename(new_path)
        LOG.info("Renamed %s -> %s", t, new_path)
        return new_path

    def batch(
        self,
        paths: Sequence[Path],
        find: str,
        replace: str,
        glob: Optional[str] = None,
        dry_run: bool = False,
    ) -> List[Tuple[Path, Path]]:
        """Batch rename by substring replacement.

        Args:
            paths: Root paths. Files are included directly. Directories include immediate children.
            find: Substring to find.
            replace: Replacement string.
            glob: Optional basename glob filter, e.g., "*.txt".
            dry_run: If True, do not modify the filesystem.

        Returns:
            List[Tuple[Path, Path]]: Pairs of (old_path, new_path) planned or applied.
        """
        results: List[Tuple[Path, Path]] = []
        for p in paths:
            root = p.expanduser().resolve()
            _confirm_exists(root)
            candidates: List[Path] = []
            if root.is_dir():
                candidates.extend(root.iterdir())
            else:
                candidates.append(root)
            for c in candidates:
                name = c.name
                if glob and not fnmatch.fnmatch(name, glob):
                    continue
                new_name = name.replace(find, replace)
                if new_name == name:
                    continue
                new_path = c.with_name(new_name)
                results.append((c, new_path))
                if not dry_run:
                    c.rename(new_path)
                    LOG.info("Renamed %s -> %s", c, new_path)
        return results


class RcloneMirror:
    """Mirror directories using `rclone`."""

    def __init__(self, tools: ToolRegistry):
        """Initialize the mirror service.

        Args:
            tools: Tool registry with optional tool paths.
        """
        self._tools = tools

    def mirror(
        self,
        src: Path,
        dst: Path,
        recursive: bool = True,
        delete_extra: bool = True,
        dry_run: bool = False,
        extra_args: Optional[Sequence[str]] = None,
    ) -> None:
        """Mirror a source to a destination using rclone.

        Args:
            src: Source path or remote.
            dst: Destination path or remote.
            recursive: Recurse into subdirectories if True.
            delete_extra: Use 'sync' semantics if True, 'copy' otherwise.
            dry_run: If True, perform a dry run.
            extra_args: Additional rclone flags.

        Raises:
            RuntimeError: If rclone is unavailable.
        """
        if not self._tools.rclone:
            raise RuntimeError("rclone not available")
        cmd: List[str] = [self._tools.rclone, "sync" if delete_extra else "copy"]
        if dry_run:
            cmd.append("--dry-run")
        if recursive:
            cmd.append("-r")
        cmd += ["--progress", "--stats-one-line", "--stats=1s"]
        if extra_args:
            cmd += list(extra_args)
        cmd += [str(src), str(dst)]
        _run_cmd(cmd)


class FileOpsApp:
    """Application facade exposing interactive and CLI interfaces."""

    def __init__(self):
        """Initialize the application and service dependencies."""
        self._tools = ToolRegistry()
        self._lister = DirectoryLister(self._tools)
        self._selector = FuzzySelector(self._tools)
        self._zoxide = ZoxideClient(self._tools)
        self._transfer = FileTransfer(LOG)
        self._rename = RenameService()
        self._mirror = RcloneMirror(self._tools)

    def run(self) -> None:
        """Run the interactive menu."""
        actions = {
            "1": ("List directory (eza if available)", self._action_list),
            "2": ("Fuzzy search (fzf if available)", self._action_search),
            "3": ("Copy with progress", self._action_copy),
            "4": ("Move with progress", self._action_move),
            "5": ("Rename single", self._action_rename_single),
            "6": ("Batch rename", self._action_rename_batch),
            "7": ("Mirror with rclone", self._action_mirror),
            "8": ("Zoxide query to pick path", self._action_zoxide_pick),
            "9": ("Exit", self._action_exit),
        }
        while True:
            print("")
            print("== FileOps ==")
            for k, (label, _) in actions.items():
                print(f"{k}. {label}")
            choice = _safe_input("Select: ")
            fn = actions.get(choice, (None, None))[1]
            if fn:
                try:
                    fn()
                except Exception as exc:
                    LOG.exception("Error: %s", exc)
                    print(f"Error: {exc}")
            else:
                print("Invalid selection")

    def cli_copy(self, args: argparse.Namespace) -> None:
        """CLI handler for copy."""
        srcs = [Path(s) for s in args.sources]
        dst = Path(args.destination)
        self._transfer.copy(
            srcs, dst, recursive=args.recursive, overwrite=args.overwrite
        )

    def cli_move(self, args: argparse.Namespace) -> None:
        """CLI handler for move."""
        srcs = [Path(s) for s in args.sources]
        dst = Path(args.destination)
        self._transfer.move(
            srcs, dst, recursive=args.recursive, overwrite=args.overwrite
        )

    def cli_list(self, args: argparse.Namespace) -> None:
        """CLI handler for list."""
        out = self._lister.list(
            Path(args.path),
            include_all=not args.no_all,
            long_format=not args.no_long,
        )
        print(out)

    def cli_mirror(self, args: argparse.Namespace) -> None:
        """CLI handler for mirror."""
        self._mirror.mirror(
            src=Path(args.src),
            dst=Path(args.dst),
            recursive=args.recursive,
            delete_extra=not args.no_delete_extra,
            dry_run=args.dry_run,
            extra_args=args.extra or None,
        )

    def cli_rename(self, args: argparse.Namespace) -> None:
        """CLI handler for rename."""
        if args.batch:
            roots = [Path(p) for p in args.paths]
            changes = self._rename.batch(
                roots,
                find=args.find,
                replace=args.replace,
                glob=args.glob,
                dry_run=args.dry_run,
            )
            for old, new in changes:
                print(f"{old} -> {new}")
        else:
            self._rename.rename(Path(args.paths[0]), args.replace)

    def _action_list(self) -> None:
        path = Path(_safe_input("Path to list: ")).expanduser()
        out = self._lister.list(path)
        print(out)

    def _action_search(self) -> None:
        root = Path(_safe_input("Search root: ")).expanduser()
        _confirm_exists(root)
        recursive = self._bool_input("Recursive [y/N]: ")
        files = [str(p) for p in _iter_paths(root, recursive=recursive)]
        sel = self._selector.choose(files, multi=True)
        print("\n".join(sel))

    def _action_copy(self) -> None:
        sources = self._collect_paths("Sources (comma-separated): ")
        dest = Path(_safe_input("Destination directory: ")).expanduser()
        recursive = self._bool_input("Recursive [Y/n]: ", default=True)
        overwrite = self._bool_input("Overwrite existing [y/N]: ", default=False)
        self._transfer.copy(sources, dest, recursive=recursive, overwrite=overwrite)

    def _action_move(self) -> None:
        sources = self._collect_paths("Sources (comma-separated): ")
        dest = Path(_safe_input("Destination directory: ")).expanduser()
        recursive = self._bool_input("Recursive [Y/n]: ", default=True)
        overwrite = self._bool_input("Overwrite existing [y/N]: ", default=False)
        self._transfer.move(sources, dest, recursive=recursive, overwrite=overwrite)

    def _action_rename_single(self) -> None:
        target = Path(_safe_input("Target path: ")).expanduser()
        new_name = _safe_input("New base name: ")
        self._rename.rename(target, new_name)

    def _action_rename_batch(self) -> None:
        roots = self._collect_paths("Paths (comma-separated; files or dirs): ")
        find = _safe_input("Find substring: ")
        replace = _safe_input("Replace with: ")
        glob = _safe_input("Optional glob filter (e.g., *.txt) or blank: ") or None
        dry = self._bool_input("Dry run [y/N]: ", default=False)
        changes = self._rename.batch(
            roots, find=find, replace=replace, glob=glob, dry_run=dry
        )
        print("Planned changes:" if dry else "Applied changes:")
        for old, new in changes:
            print(f"{old} -> {new}")

    def _action_mirror(self) -> None:
        src = Path(_safe_input("Source (local path OK): ")).expanduser()
        dst = Path(_safe_input("Destination (local path OK): ")).expanduser()
        recursive = self._bool_input("Recursive [Y/n]: ", default=True)
        delete_extra = self._bool_input(
            "Delete extras at destination [Y/n]: ", default=True
        )
        dry = self._bool_input("Dry run [y/N]: ", default=False)
        self._mirror.mirror(
            src=src,
            dst=dst,
            recursive=recursive,
            delete_extra=delete_extra,
            dry_run=dry,
        )

    def _action_zoxide_pick(self) -> None:
        pattern = _safe_input("zoxide pattern: ")
        paths = self._zoxide.query(pattern)
        if not paths:
            print("No matches")
            return
        choice = self._selector.choose(paths, multi=False)
        print(choice[0] if choice else "No selection")

    def _action_exit(self) -> None:
        print("Bye")
        sys.exit(0)

    def _collect_paths(self, prompt: str) -> List[Path]:
        """Parse a comma-separated list of paths from input.

        Args:
            prompt: Input prompt.

        Returns:
            List[Path]: Expanded user paths.
        """
        raw = _safe_input(prompt)
        parts = [p.strip() for p in raw.split(",") if p.strip()]
        return [Path(p).expanduser() for p in parts]

    def _bool_input(self, prompt: str, default: bool = False) -> bool:
        """Parse a boolean response from input.

        Args:
            prompt: Input prompt.
            default: Default value if input is empty.

        Returns:
            bool: Parsed boolean value.
        """
        s = _safe_input(prompt).lower()
        if not s:
            return default
        return s in {"y", "yes", "1", "true", "t"}


def _build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser.

    Returns:
        argparse.ArgumentParser: Parser with subcommands.
    """
    p = argparse.ArgumentParser(
        prog="fileops",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """\
            FileOps: interactive and CLI file utility

            Modes:
              1) Interactive: run with no subcommand.
              2) Non-interactive: use subcommands below.
            """
        ),
    )
    sub = p.add_subparsers(dest="cmd")

    sp = sub.add_parser("list", help="List a directory")
    sp.add_argument("path")
    sp.add_argument("--no-all", action="store_true", help="Hide dotfiles")
    sp.add_argument("--no-long", action="store_true", help="Short format")
    sp.set_defaults(handler="list")

    sp = sub.add_parser("copy", help="Copy with progress")
    sp.add_argument("destination")
    sp.add_argument("sources", nargs="+")
    sp.add_argument("-r", "--recursive", action="store_true")
    sp.add_argument("-f", "--overwrite", action="store_true")
    sp.set_defaults(handler="copy")

    sp = sub.add_parser("move", help="Move with progress")
    sp.add_argument("destination")
    sp.add_argument("sources", nargs="+")
    sp.add_argument("-r", "--recursive", action="store_true")
    sp.add_argument("-f", "--overwrite", action="store_true")
    sp.set_defaults(handler="move")

    sp = sub.add_parser("mirror", help="Mirror with rclone")
    sp.add_argument("src")
    sp.add_argument("dst")
    sp.add_argument("-r", "--recursive", action="store_true", default=True)
    sp.add_argument(
        "--no-delete-extra", action="store_true", help="Do not delete extras at dst"
    )
    sp.add_argument("--dry-run", action="store_true")
    sp.add_argument("--extra", nargs="*", help="Extra rclone flags")
    sp.set_defaults(handler="mirror")

    sp = sub.add_parser("rename", help="Rename single or batch")
    sp.add_argument("paths", nargs="+", help="Targets (file or directory)")
    sp.add_argument("--find", help="Substring to find (batch mode)")
    sp.add_argument("--replace", required=True, help="Replacement or new name")
    sp.add_argument("--glob", help="Optional glob for batch filter")
    sp.add_argument("--dry-run", action="store_true")
    sp.add_argument("--batch", action="store_true", help="Enable batch mode")
    sp.set_defaults(handler="rename")

    return p


def main(argv: Optional[Sequence[str]] = None) -> None:
    """Program entry point.

    Args:
        argv: Optional argument vector. Defaults to sys.argv[1:].
    """
    app = FileOpsApp()
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not args.cmd:
        app.run()
        return
    handler = getattr(app, f"cli_{args.handler}", None)
    if not handler:
        raise SystemExit(f"Unknown handler: {args.handler}")
    handler(args)


if __name__ == "__main__":
    main()
