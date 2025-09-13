#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NFO Renamer
Pure OOP tool to align `.nfo` filenames with the single video file in each subdirectory.
Supports dry runs, colorized output (Catppuccin Mocha), and forced overwrite on conflicts.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple


class ColorTheme:
    """Catppuccin Mocha 24-bit ANSI theme.

    Attributes:
        reset: Reset sequence.
        bold: Bold sequence.
        info: Primary info color.
        warn: Warning color.
        err: Error color.
        ok: Success color.
        muted: Low-contrast detail color.
        action: Action highlight color.
        header: Section header color.
    """

    # Hex palette (Catppuccin Mocha)
    _rosewater = (245, 224, 220)
    _flamingo = (242, 205, 205)
    _pink = (245, 194, 231)
    _mauve = (203, 166, 247)
    _red = (243, 139, 168)
    _maroon = (235, 160, 172)
    _peach = (250, 179, 135)
    _yellow = (249, 226, 175)
    _green = (166, 227, 161)
    _teal = (148, 226, 213)
    _sky = (137, 220, 235)
    _sapphire = (116, 199, 236)
    _blue = (137, 180, 250)
    _lavender = (180, 190, 254)
    _text = (205, 214, 244)
    _subtext0 = (127, 132, 156)

    def __init__(self) -> None:
        self.reset = "\x1b[0m"
        self.bold = "\x1b[1m"
        self.info = self._fg(self._blue)
        self.warn = self._fg(self._peach)
        self.err = self._fg(self._red)
        self.ok = self._fg(self._green)
        self.muted = self._fg(self._subtext0)
        self.action = self._fg(self._mauve)
        self.header = self._fg(self._lavender)

    @staticmethod
    def _fg(rgb: Tuple[int, int, int]) -> str:
        r, g, b = rgb
        return f"\x1b[38;2;{r};{g};{b}m"


class Console:
    """Console utilities for colored output.

    Args:
        theme: ColorTheme instance.
        enable_color: If False, emit plain text.
    """

    def __init__(
        self, theme: Optional[ColorTheme] = None, enable_color: bool = True
    ) -> None:
        self.theme = theme or ColorTheme()
        self.enable_color = enable_color

    def _c(self, text: str, color: str) -> str:
        if not self.enable_color:
            return text
        return f"{color}{text}{self.theme.reset}"

    def bold(self, text: str) -> str:
        if not self.enable_color:
            return text
        return f"{self.theme.bold}{text}{self.theme.reset}"

    def info(self, text: str) -> str:
        return self._c(text, self.theme.info)

    def warn(self, text: str) -> str:
        return self._c(text, self.theme.warn)

    def err(self, text: str) -> str:
        return self._c(text, self.theme.err)

    def ok(self, text: str) -> str:
        return self._c(text, self.theme.ok)

    def muted(self, text: str) -> str:
        return self._c(text, self.theme.muted)

    def action(self, text: str) -> str:
        return self._c(text, self.theme.action)

    def header(self, text: str) -> str:
        return self._c(text, self.theme.header)


class RenamePlanItem:
    """Single planned operation for an .nfo file.

    Args:
        directory: Parent directory.
        current_nfo: Path to the existing .nfo file.
        video_file: Matching video file.
        target_nfo: Computed target .nfo path.
        conflict: Target already exists and is different from current_nfo.
        already_correct: True if current_nfo already matches the video stem.
    """

    def __init__(
        self,
        directory: Path,
        current_nfo: Path,
        video_file: Path,
    ) -> None:
        self.directory = directory
        self.current_nfo = current_nfo
        self.video_file = video_file
        self.target_nfo = directory / (video_file.stem + ".nfo")
        self.conflict = self.target_nfo.exists() and self.target_nfo != self.current_nfo
        self.already_correct = self.current_nfo.name == self.target_nfo.name

    def action_label(self, force: bool) -> str:
        if self.already_correct:
            return "noop"
        if self.conflict and not force:
            return "conflict-skip"
        if self.conflict and force:
            return "overwrite"
        return "rename"


class NFORenamer:
    """Engine to discover and apply .nfo rename operations.

    This class scans a base directory for subdirectories that contain exactly one
    video file and one or more .nfo files. It plans and applies renames so each
    .nfo matches the video filename stem.

    Args:
        base_directory: Directory to scan.
        force: If True, overwrite conflicting .nfo files.
        console: Console instance for output. If None, a default is used.

    Attributes:
        video_extensions: Recognized video file extensions.
        nfo_extension: The .nfo extension string.
    """

    video_extensions: Sequence[str] = (".mkv", ".mp4")
    nfo_extension: str = ".nfo"

    def __init__(
        self,
        base_directory: str = ".",
        force: bool = False,
        console: Optional[Console] = None,
    ) -> None:
        self.base_directory = Path(base_directory).resolve()
        self.force = force
        self.console = console or Console()

    def _iter_subdirs(self) -> Iterable[Path]:
        """Yield subdirectories directly under base_directory."""
        if not self.base_directory.exists():
            raise FileNotFoundError(f"Directory not found: {self.base_directory}")
        for p in sorted(self.base_directory.iterdir()):
            if p.is_dir():
                yield p

    def _scan_dir(self, directory: Path) -> Tuple[List[Path], List[Path]]:
        """Collect video and .nfo files in a directory.

        Args:
            directory: Directory to scan.

        Returns:
            Pair of lists: (video_files, nfo_files).
        """
        videos: List[Path] = []
        nfos: List[Path] = []
        for f in sorted(directory.iterdir()):
            if not f.is_file():
                continue
            suf = f.suffix.lower()
            if suf in self.video_extensions:
                videos.append(f)
            elif suf == self.nfo_extension:
                nfos.append(f)
        return videos, nfos

    def plan(self) -> Tuple[List[RenamePlanItem], List[str]]:
        """Build a full plan across all subdirectories.

        Returns:
            A tuple with:
            - list of planned items for every discovered .nfo (including noops and conflicts),
            - list of directory-level warnings (e.g., multiple videos).
        """
        items: List[RenamePlanItem] = []
        warnings: List[str] = []

        for d in self._iter_subdirs():
            videos, nfos = self._scan_dir(d)

            if len(videos) == 0 and len(nfos) > 0:
                warnings.append(
                    f"No video files in '{d.name}', {len(nfos)} .nfo file(s) present"
                )
            if len(videos) > 1:
                warnings.append(
                    f"Multiple video files in '{d.name}', skipping directory"
                )

            if len(videos) == 1 and nfos:
                v = videos[0]
                for n in nfos:
                    items.append(RenamePlanItem(d, n, v))

        return items, warnings

    def show(
        self, items: List[RenamePlanItem], warnings: List[str], dry_run: bool
    ) -> None:
        """Render a detailed preview or execution log.

        Args:
            items: Planned operations.
            warnings: Directory-level warnings.
            dry_run: If True, indicate preview mode.
        """
        hdr = "DRY RUN" if dry_run else "EXECUTE"
        print(self.console.header(self.console.bold(f"\nNFO Renamer · {hdr}")))
        print(self.console.muted(f"Base: {self.base_directory}   Force: {self.force}"))
        print(
            self.console.muted(
                "Rules: exactly one video per folder; rename all .nfo to match video stem\n"
            )
        )

        if warnings:
            print(self.console.warn("Directory issues:"))
            for w in warnings:
                print(f"  - {w}")
            print()

        if not items:
            print(
                self.console.info(
                    "No .nfo files need renaming or there are no eligible directories."
                )
            )
            return

        print(self.console.header("Planned items:"))
        for i, it in enumerate(items, 1):
            act = it.action_label(self.force)
            if act == "noop":
                act_str = self.console.muted("[ok] already named")
            elif act == "rename":
                act_str = self.console.action("[rename]")
            elif act == "overwrite":
                act_str = self.console.ok("[overwrite]")
            else:
                act_str = self.console.warn("[conflict-skip]")

            print(f"{i:3d}. {act_str} {self.console.bold(it.directory.name)}")
            print(f"     nfo:   {it.current_nfo.name}")
            print(f"     video: {it.video_file.name}")
            print(f"     ->     {it.target_nfo.name}")
            if it.conflict and not it.already_correct:
                msg = "target exists"
                print(f"     note:  {self.console.warn(msg)}")
            print()

        if dry_run:
            print(
                self.console.muted(
                    "Nothing changed. Use --execute to apply. Use --force to overwrite conflicts."
                )
            )

    def apply(self, items: List[RenamePlanItem]) -> Tuple[int, int]:
        """Apply the planned operations.

        Args:
            items: Planned operations.

        Returns:
            A pair (success_count, total_attempted) for non-noop actions.
        """
        success = 0
        attempted = 0

        for it in items:
            act = it.action_label(self.force)
            if act == "noop":
                continue

            attempted += 1
            try:
                if it.conflict and self.force:
                    # Replace target with the current file atomically where supported.
                    it.current_nfo.replace(it.target_nfo)
                elif it.conflict and not self.force:
                    print(
                        self.console.warn(
                            f"skip: {it.directory.name} → {it.target_nfo.name} (conflict)"
                        )
                    )
                    continue
                else:
                    # No conflict. Simple rename.
                    it.current_nfo.rename(it.target_nfo)
                print(
                    self.console.ok(f"done: {it.directory.name} → {it.target_nfo.name}")
                )
                success += 1
            except Exception as exc:
                print(
                    self.console.err(
                        f"fail: {it.directory.name} → {it.target_nfo.name}: {exc}"
                    )
                )

        return success, attempted


class NFORenamerApp:
    """CLI façade around NFORenamer using pure OOP entrypoints."""

    def __init__(self, argv: Optional[Sequence[str]] = None) -> None:
        self.argv = list(argv) if argv is not None else sys.argv[1:]
        self.console = Console()

    def build_parser(self) -> argparse.ArgumentParser:
        """Build an argument parser."""
        parser = argparse.ArgumentParser(
            description="Rename .nfo files to match the single video file per directory.",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=(
                "Examples:\n"
                "  nfo_renamer.py                       # Interactive preview then prompt\n"
                "  nfo_renamer.py --dry-run             # Preview only\n"
                "  nfo_renamer.py --execute             # Apply changes\n"
                "  nfo_renamer.py -d /path --force      # Apply and overwrite on conflicts\n"
            ),
        )
        parser.add_argument(
            "-d", "--directory", default=".", help="Root directory to scan"
        )
        mode = parser.add_mutually_exclusive_group()
        mode.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview operations without changing files",
        )
        mode.add_argument(
            "--execute", action="store_true", help="Apply file operations"
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Overwrite existing conflicting .nfo files",
        )
        parser.add_argument(
            "--no-color", action="store_true", help="Disable ANSI color output"
        )
        return parser

    def run(self) -> int:
        """Run the app."""
        parser = self.build_parser()
        args = parser.parse_args(self.argv)

        # Update console color setting
        self.console.enable_color = not args.no_color

        engine = NFORenamer(
            base_directory=args.directory, force=args.force, console=self.console
        )

        try:
            items, warnings = engine.plan()
            # Always show a full plan, including noops and conflicts.
            engine.show(items, warnings, dry_run=not args.execute)

            if not args.execute:
                return 0

            success, attempted = engine.apply(items)
            print(
                self.console.muted(
                    f"\nSummary: {success}/{attempted} operation(s) succeeded"
                )
            )
            return 0 if success == attempted else 2

        except KeyboardInterrupt:
            print(self.console.warn("\nInterrupted"))
            return 130
        except Exception as exc:
            print(self.console.err(f"Error: {exc}"))
            return 1


def main() -> None:
    """Module entrypoint."""
    raise SystemExit(NFORenamerApp().run())


if __name__ == "__main__":
    main()
