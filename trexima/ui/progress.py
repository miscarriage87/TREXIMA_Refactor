"""
Progress Tracker Module

Handles progress tracking and logging.
"""

import time
from typing import Optional, Callable, List
import tkinter as tk
from tkinter import ttk


class ProgressTracker:
    """Tracks and displays progress of operations."""

    def __init__(
        self,
        parent: Optional[tk.Widget] = None,
        trough_color: str = "white",
        bar_color: str = "#90ee90"
    ):
        self.parent = parent
        self.trough_color = trough_color
        self.bar_color = bar_color

        self.progress_bar: Optional[ttk.Progressbar] = None
        self.style: Optional[ttk.Style] = None
        self.log_entries: List[str] = []
        self.current_value: int = 0
        self.current_message: str = ""

        self._callbacks: List[Callable[[int, str], None]] = []

        if parent:
            self._setup_progress_bar()

    def _setup_progress_bar(self):
        """Set up the progress bar widget."""
        if not self.parent:
            return

        self.style = ttk.Style(self.parent)

        # Custom progress bar layout with label
        self.style.layout(
            "LabeledProgressbar",
            [
                ("LabeledProgressbar.trough", {
                    "children": [
                        ("LabeledProgressbar.pbar", {"side": "left", "sticky": "ns"}),
                        ("LabeledProgressbar.label", {"sticky": ""})
                    ],
                    "sticky": "nswe"
                })
            ]
        )

        self.progress_bar = ttk.Progressbar(
            self.parent,
            orient=tk.HORIZONTAL,
            length=800,
            mode="determinate",
            style="LabeledProgressbar",
            maximum=100
        )

    def show(self, x: float = 0.10, y: float = 0.80, width: float = 0.8, height: float = 0.05):
        """Show the progress bar."""
        if self.progress_bar:
            self.progress_bar.place(relx=x, rely=y, relwidth=width, relheight=height)

    def hide(self):
        """Hide the progress bar."""
        if self.progress_bar:
            self.progress_bar.place_forget()

    def update(self, percent: int, message: str):
        """
        Update progress.

        Args:
            percent: Progress percentage (0-100)
            message: Status message
        """
        self.current_value = percent
        self.current_message = message

        # Log the progress
        timestamp = time.strftime("%a_%d%b_%Y_%Hh%Mm%Ss", time.localtime())
        self.log_entries.append(f"{timestamp}: {message}")

        # Update UI if available
        if self.progress_bar and self.style:
            self.progress_bar["value"] = percent
            self.style.configure(
                "LabeledProgressbar",
                text=message,
                troughcolor=self.trough_color,
                bordercolor=self.trough_color,
                background=self.bar_color,
                lightcolor=self.bar_color,
                darkcolor=self.bar_color
            )

            if self.parent:
                self.parent.update()

        # Notify callbacks
        for callback in self._callbacks:
            callback(percent, message)

    def reset(self, message: str = "Ready"):
        """Reset progress to zero."""
        self.update(0, message)

    def complete(self, message: str = "Complete"):
        """Set progress to 100%."""
        self.update(100, message)

    def add_callback(self, callback: Callable[[int, str], None]):
        """
        Add a progress callback.

        Args:
            callback: Function that takes (percent, message)
        """
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[int, str], None]):
        """Remove a progress callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def get_log(self) -> str:
        """Get the complete progress log."""
        return "\n\n".join(self.log_entries)

    def clear_log(self):
        """Clear the progress log."""
        self.log_entries = []

    def get_current_progress(self) -> tuple:
        """Get current progress value and message."""
        return self.current_value, self.current_message


class StepTracker:
    """Tracks multi-step operations."""

    def __init__(
        self,
        total_steps: int,
        progress_tracker: Optional[ProgressTracker] = None
    ):
        self.total_steps = total_steps
        self.current_step = 0
        self.progress_tracker = progress_tracker
        self.step_names: List[str] = []

    def set_steps(self, step_names: List[str]):
        """Set the step names."""
        self.step_names = step_names
        self.total_steps = len(step_names)

    def next_step(self, message: Optional[str] = None):
        """Move to the next step."""
        self.current_step += 1

        if message is None and self.current_step <= len(self.step_names):
            message = self.step_names[self.current_step - 1]

        if self.progress_tracker:
            percent = int((self.current_step / self.total_steps) * 100)
            self.progress_tracker.update(percent, message or f"Step {self.current_step}")

    def complete(self, message: str = "All steps complete"):
        """Mark all steps as complete."""
        self.current_step = self.total_steps
        if self.progress_tracker:
            self.progress_tracker.complete(message)

    def reset(self):
        """Reset step tracking."""
        self.current_step = 0
        if self.progress_tracker:
            self.progress_tracker.reset()

    def get_progress_percent(self) -> int:
        """Get current progress as percentage."""
        if self.total_steps == 0:
            return 0
        return int((self.current_step / self.total_steps) * 100)
