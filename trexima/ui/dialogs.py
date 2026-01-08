"""
Dialog Manager Module

Handles various dialog interactions.
"""

import os
from typing import List, Optional, Tuple, Dict, Any
import tkinter as tk
from tkinter import filedialog, messagebox
import easygui as gui


class DialogManager:
    """Manages dialog interactions for the application."""

    def __init__(self, default_dir: str = None):
        self.default_dir = default_dir or os.getcwd()

    def set_default_directory(self, directory: str):
        """Set the default directory for file dialogs."""
        self.default_dir = directory

    def show_message(
        self,
        title: str,
        text: str,
        option: str = None
    ) -> Optional[bool]:
        """
        Show a message dialog.

        Args:
            title: Dialog title
            text: Message text
            option: Dialog type (None, YESNO, RETRYCANCEL, OKCANCEL, INFO, WARNING, ERROR)

        Returns:
            Boolean for question dialogs, None for info dialogs
        """
        root = tk.Tk()
        root.withdraw()

        result = None
        mb = messagebox

        if option == "YESNO":
            result = mb.askyesno(title, text)
        elif option == "RETRYCANCEL":
            result = mb.askretrycancel(title, text)
        elif option == "OKCANCEL":
            result = mb.askokcancel(title, text)
        elif option == "INFO" or option is None:
            mb.showinfo(title, text)
        elif option == "WARNING":
            mb.showwarning(title, text)
        elif option == "ERROR":
            mb.showerror(title, text)

        root.destroy()
        return result

    def show_info(self, title: str, message: str):
        """Show an info message."""
        self.show_message(title, message, "INFO")

    def show_warning(self, title: str, message: str):
        """Show a warning message."""
        self.show_message(title, message, "WARNING")

    def show_error(self, title: str, message: str):
        """Show an error message."""
        self.show_message(title, message, "ERROR")

    def ask_yes_no(self, title: str, question: str) -> bool:
        """Ask a yes/no question."""
        return self.show_message(title, question, "YESNO") or False

    def ask_ok_cancel(self, title: str, question: str) -> bool:
        """Ask an OK/Cancel question."""
        return self.show_message(title, question, "OKCANCEL") or False

    def select_files(
        self,
        title: str = "Select Files",
        file_types: List[Tuple[str, str]] = None,
        multiple: bool = True
    ) -> List[str]:
        """
        Open a file selection dialog.

        Args:
            title: Dialog title
            file_types: List of (description, pattern) tuples
            multiple: Allow multiple file selection

        Returns:
            List of selected file paths
        """
        if file_types is None:
            file_types = [("All Files", "*.*")]

        root = tk.Tk()
        root.withdraw()

        if multiple:
            files = filedialog.askopenfilenames(
                initialdir=self.default_dir,
                title=title,
                filetypes=file_types
            )
        else:
            file = filedialog.askopenfilename(
                initialdir=self.default_dir,
                title=title,
                filetypes=file_types
            )
            files = [file] if file else []

        root.destroy()
        return list(files)

    def select_xml_files(self, title: str = "Open XML Files") -> List[str]:
        """Select XML files."""
        return self.select_files(title, [("XML File", "*.xml")])

    def select_excel_file(self, title: str = "Open Excel File") -> Optional[str]:
        """Select a single Excel file."""
        files = self.select_files(
            title,
            [("Excel File", "*.xlsx")],
            multiple=False
        )
        return files[0] if files else None

    def select_csv_file(self, title: str = "Open CSV File") -> Optional[str]:
        """Select a single CSV file."""
        files = self.select_files(
            title,
            [("CSV File", "*.csv")],
            multiple=False
        )
        return files[0] if files else None

    def save_file(
        self,
        title: str = "Save File",
        default_name: str = "",
        file_types: List[Tuple[str, str]] = None
    ) -> Optional[str]:
        """
        Open a save file dialog.

        Args:
            title: Dialog title
            default_name: Default filename
            file_types: List of (description, pattern) tuples

        Returns:
            Selected file path or None
        """
        if file_types is None:
            file_types = [("All Files", "*.*")]

        default_path = os.path.join(self.default_dir, default_name)

        return gui.filesavebox(
            msg=title,
            title="Save As",
            default=default_path
        )

    def multi_choice(
        self,
        message: str,
        title: str,
        choices: List[str],
        preselect: List[int] = None
    ) -> Optional[List[str]]:
        """
        Show a multi-selection choice dialog.

        Args:
            message: Dialog message
            title: Dialog title
            choices: List of choices
            preselect: List of indices to preselect

        Returns:
            List of selected choices or None
        """
        if preselect is None:
            preselect = list(range(len(choices)))

        return gui.multchoicebox(message, title, choices, preselect)

    def single_choice(
        self,
        message: str,
        title: str,
        choices: List[str],
        default_index: int = 0
    ) -> Optional[str]:
        """
        Show a single-selection choice dialog.

        Args:
            message: Dialog message
            title: Dialog title
            choices: List of choices
            default_index: Default selection index

        Returns:
            Selected choice or None
        """
        return gui.choicebox(message, title, choices, default_index)

    def get_credentials(
        self,
        message: str,
        title: str,
        fields: List[str],
        defaults: List[str] = None
    ) -> Optional[List[str]]:
        """
        Show a password entry dialog.

        Args:
            message: Dialog message
            title: Dialog title
            fields: List of field names
            defaults: List of default values

        Returns:
            List of entered values or None
        """
        if defaults is None:
            defaults = [""] * len(fields)

        return gui.multpasswordbox(message, title, fields, defaults)

    def show_text(
        self,
        message: str,
        title: str,
        text: str
    ):
        """
        Show a text viewing dialog.

        Args:
            message: Dialog message
            title: Dialog title
            text: Text content to display
        """
        gui.textbox(msg=message, title=title, text=text)

    def get_odata_credentials(
        self,
        defaults: Dict[str, str] = None
    ) -> Optional[Dict[str, str]]:
        """
        Get OData API credentials from user.

        Args:
            defaults: Default values for fields

        Returns:
            Dictionary with credentials or None
        """
        if defaults is None:
            defaults = {
                "service_url": "https://api.successfactors.eu/odata/v2",
                "company_id": "",
                "username": "",
                "password": ""
            }

        fields = [
            "SF OData Service URL",
            "Company ID",
            "API Username",
            "Password"
        ]

        default_values = [
            defaults.get("service_url", ""),
            defaults.get("company_id", ""),
            defaults.get("username", ""),
            defaults.get("password", "")
        ]

        values = self.get_credentials(
            "Enter SF OData API Connection Details",
            "SF OData Connection",
            fields,
            default_values
        )

        if values is None:
            return None

        # Validate all fields are filled
        for i, field in enumerate(fields):
            if not values[i].strip():
                self.show_error("Validation Error", f"{field} is required.")
                return self.get_odata_credentials(defaults)

        return {
            "service_url": values[0],
            "company_id": values[1],
            "username": values[2],
            "password": values[3]
        }

    def select_locales(
        self,
        available_locales: List[str],
        title: str = "Select Locales for Export"
    ) -> List[str]:
        """
        Show locale selection dialog.

        Args:
            available_locales: List of available locale codes
            title: Dialog title

        Returns:
            List of selected locale codes
        """
        selected = self.multi_choice(
            "Choose Locales for the export of translations",
            title,
            available_locales,
            list(range(len(available_locales)))
        )
        return selected if selected else available_locales

    def select_default_language(
        self,
        locales: List[str],
        default: str = "en_US"
    ) -> str:
        """
        Select default language from available locales.

        Args:
            locales: Available locale codes
            default: Default selection

        Returns:
            Selected locale code
        """
        default_index = 0
        if default in locales:
            default_index = locales.index(default)

        result = self.single_choice(
            "Choose SF instance's Default Language",
            "Default Language",
            locales,
            default_index
        )
        return result if result else default
