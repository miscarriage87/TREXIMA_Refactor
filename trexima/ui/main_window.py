"""
Main Window Module

Main Tkinter application window.
"""

import os
import tkinter as tk
from tkinter import ttk, PhotoImage
from typing import Optional, Callable

try:
    from ttkthemes import ThemedTk
except ImportError:
    ThemedTk = None

from ..config import (
    APP_NAME,
    VERSION,
    APP_TITLE,
    BG_COLOR,
    AppPaths
)
from .dialogs import DialogManager
from .progress import ProgressTracker


class MainWindow:
    """Main application window."""

    def __init__(self, app_paths: Optional[AppPaths] = None):
        self.app_paths = app_paths or AppPaths()
        self.dialog_manager = DialogManager()

        # Create main window
        if ThemedTk:
            self.root = ThemedTk(theme="elegance")
        else:
            self.root = tk.Tk()

        self.root.title(APP_TITLE)
        self.root.geometry("1200x700")
        self.root.config(background=BG_COLOR)

        # Try to maximize window
        try:
            self.root.state("zoomed")
        except tk.TclError:
            pass

        # Load icons
        self._load_icons()

        # Set up background
        self._setup_background()

        # Create progress tracker
        self.progress_tracker = ProgressTracker(self.root)
        self.progress_tracker.show()

        # UI elements
        self.file_open_btn: Optional[ttk.Button] = None
        self.connect_api_btn: Optional[ttk.Button] = None
        self.export_execute_btn: Optional[ttk.Button] = None
        self.import_execute_btn: Optional[ttk.Button] = None

        # Callbacks
        self._on_export: Optional[Callable] = None
        self._on_import: Optional[Callable] = None
        self._on_open_files: Optional[Callable] = None
        self._on_connect_api: Optional[Callable] = None
        self._on_execute_export: Optional[Callable] = None
        self._on_execute_import: Optional[Callable] = None

        # State
        self.is_export_action = False

        # Set up menu and main buttons
        self._setup_menu()
        self._setup_main_buttons()

    def _load_icons(self):
        """Load application icons."""
        try:
            self.app_icon = PhotoImage(file=self.app_paths.app_icon_path)
            self.root.iconphoto(False, self.app_icon)
        except Exception:
            self.app_icon = None

        try:
            self.done_icon = PhotoImage(file=self.app_paths.done_icon_path)
        except Exception:
            self.done_icon = None

    def _setup_background(self):
        """Set up background image."""
        try:
            self.bg_image = PhotoImage(file=self.app_paths.background_image_path)
            self.bg_label = tk.Label(self.root, image=self.bg_image)
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception:
            pass

    def _setup_menu(self):
        """Set up application menu."""
        menubar = tk.Menu(self.root)

        # Actions menu
        action_menu = tk.Menu(menubar, tearoff=False)
        action_menu.add_command(
            label="Export Translations",
            command=self._start_export
        )
        action_menu.add_command(
            label="Generate Import Configs For Translation",
            command=self._start_import
        )
        action_menu.add_separator()
        action_menu.add_command(
            label="Reset Import/Export Progress",
            command=self._reset_progress
        )
        menubar.add_cascade(label="Actions", menu=action_menu)

        # About menu
        about_menu = tk.Menu(menubar, tearoff=False)
        about_menu.add_command(
            label=f"Using {APP_NAME}",
            command=self._show_help
        )
        about_menu.add_command(
            label=f"About {APP_NAME}",
            command=self._show_about
        )
        about_menu.add_separator()
        about_menu.add_command(
            label=f"Quit {APP_NAME}",
            command=self.root.quit
        )
        menubar.add_cascade(label="About", menu=about_menu)

        self.root.config(menu=menubar)

    def _setup_main_buttons(self):
        """Set up main action buttons."""
        # Export button
        export_btn = ttk.Button(
            self.root,
            text="Export Translations",
            command=self._start_export
        )
        export_btn.place(relx=0.25, rely=0.01, relwidth=0.2, relheight=0.05)

        # Import button
        import_btn = ttk.Button(
            self.root,
            text="Generate Import Configs For Translation",
            command=self._start_import
        )
        import_btn.place(relx=0.55, rely=0.01, relwidth=0.2, relheight=0.05)

        # View progress log button
        log_btn = ttk.Button(
            self.root,
            text="View Progress Log",
            command=self._view_progress_log
        )
        log_btn.place(relx=0.40, rely=0.90, relwidth=0.2, relheight=0.05)

    def _start_export(self):
        """Start export workflow."""
        self.is_export_action = True

        # Create step buttons
        self.file_open_btn = ttk.Button(
            self.root,
            text="1. Open Configuration XML File(s)",
            command=self._handle_open_files
        )
        self.file_open_btn.place(relx=0.25, rely=0.1, relwidth=0.2, relheight=0.05)

        self.connect_api_btn = ttk.Button(
            self.root,
            text="2. Connect To SF OData Service",
            command=self._handle_connect_api
        )
        self.connect_api_btn.place(relx=0.25, rely=0.2, relwidth=0.2, relheight=0.05)

        if self._on_export:
            self._on_export()

    def _start_import(self):
        """Start import workflow."""
        self.is_export_action = False

        if self._on_import:
            self._on_import()

    def setup_import_buttons(self, text: str = "1. Browse to Latest Data Model File(s)"):
        """Set up import step buttons."""
        self.file_open_btn = ttk.Button(
            self.root,
            text=text,
            command=self._handle_open_files
        )
        self.file_open_btn.place(relx=0.55, rely=0.1, relwidth=0.2, relheight=0.05)

        self.connect_api_btn = ttk.Button(
            self.root,
            text="2. Connect SF OData Service",
            command=self._handle_connect_api
        )
        self.connect_api_btn.place(relx=0.55, rely=0.2, relwidth=0.2, relheight=0.05)

    def show_execute_button(self):
        """Show the execute button based on current action."""
        if self.is_export_action:
            self.export_execute_btn = ttk.Button(
                self.root,
                text="3. Now Execute Export",
                command=self._handle_execute_export
            )
            self.export_execute_btn.place(relx=0.25, rely=0.3, relwidth=0.2, relheight=0.05)
            self.progress_tracker.update(100, "Translations can now be exported!")
        else:
            self.import_execute_btn = ttk.Button(
                self.root,
                text="3. Now Execute Import",
                command=self._handle_execute_import
            )
            self.import_execute_btn.place(relx=0.55, rely=0.3, relwidth=0.2, relheight=0.05)
            self.progress_tracker.update(100, "Translations can now be imported!")

    def mark_step_complete(self, button: ttk.Button):
        """Mark a step button as complete."""
        if button and self.done_icon:
            button["state"] = "disabled"
            button["image"] = self.done_icon
            button["compound"] = tk.LEFT

    def _handle_open_files(self):
        """Handle open files button click."""
        if self._on_open_files:
            self._on_open_files()

    def _handle_connect_api(self):
        """Handle connect API button click."""
        if self._on_connect_api:
            self._on_connect_api()

    def _handle_execute_export(self):
        """Handle execute export button click."""
        if self._on_execute_export:
            self._on_execute_export()

    def _handle_execute_import(self):
        """Handle execute import button click."""
        if self._on_execute_import:
            self._on_execute_import()

    def _reset_progress(self):
        """Reset current operation progress."""
        if self.file_open_btn:
            self.file_open_btn.place_forget()
        if self.connect_api_btn:
            self.connect_api_btn.place_forget()
        if self.export_execute_btn:
            self.export_execute_btn.place_forget()
        if self.import_execute_btn:
            self.import_execute_btn.place_forget()

        msg = "Export" if self.is_export_action else "Import"
        self.progress_tracker.reset(f"The 'in-progress' Translations {msg} has been reset!")

    def _view_progress_log(self):
        """View the progress log."""
        log_text = self.progress_tracker.get_log()
        self.dialog_manager.show_text(
            "Following are the activities you have performed till now",
            f"{APP_NAME} - Progress Log",
            log_text
        )

    def _show_about(self):
        """Show about dialog."""
        self.dialog_manager.show_info(
            f"About {APP_NAME}",
            f"{APP_NAME} Version {VERSION}"
        )

    def _show_help(self):
        """Show help dialog."""
        help_text = (
            f"{APP_NAME} is an acceleration application to easily manage "
            "translations of various translatable UI elements in SAP SuccessFactors.\n\n"
            "It hugely reduces the manual effort needed in documenting the "
            "translations workbook as well as in preparing the configuration "
            "elements for importing translations."
        )
        self.dialog_manager.show_info(f"{APP_NAME} - HELP", help_text)

    def set_on_export(self, callback: Callable):
        """Set export start callback."""
        self._on_export = callback

    def set_on_import(self, callback: Callable):
        """Set import start callback."""
        self._on_import = callback

    def set_on_open_files(self, callback: Callable):
        """Set open files callback."""
        self._on_open_files = callback

    def set_on_connect_api(self, callback: Callable):
        """Set connect API callback."""
        self._on_connect_api = callback

    def set_on_execute_export(self, callback: Callable):
        """Set execute export callback."""
        self._on_execute_export = callback

    def set_on_execute_import(self, callback: Callable):
        """Set execute import callback."""
        self._on_execute_import = callback

    def run(self):
        """Start the main event loop."""
        self.progress_tracker.update(
            0,
            f"{APP_NAME} is ready for export or import of applicable translations configuration artifacts!"
        )
        self.root.mainloop()

    def update(self):
        """Update the UI."""
        self.root.update()

    def update_idletasks(self):
        """Update idle tasks."""
        self.root.update_idletasks()
