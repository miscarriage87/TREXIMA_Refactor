"""
CSV Handler Module

Handles reading and writing of CSV files.
"""

import csv
import time
import os
from typing import List, Dict, Optional, Any


class CSVHandler:
    """Handles CSV file operations."""

    def __init__(self, encoding: str = "utf-8"):
        self.encoding = encoding

    def read_csv_as_matrix(self, file_path: str) -> List[List[str]]:
        """
        Read a CSV file and return as a matrix (list of lists).

        Args:
            file_path: Path to the CSV file

        Returns:
            List of rows, each row is a list of values
        """
        values_matrix = []
        with open(file_path, newline="", encoding=self.encoding) as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                values_matrix.append(row)
        return values_matrix

    def read_csv_as_dict_list(
        self,
        file_path: str
    ) -> tuple[List[Dict[str, str]], List[str]]:
        """
        Read a CSV file and return as a list of dictionaries.

        Args:
            file_path: Path to the CSV file

        Returns:
            Tuple of (list of row dictionaries, list of headers)
        """
        rows = []
        headers = []
        with open(file_path, newline="", encoding=self.encoding) as csvfile:
            reader = csv.DictReader(csvfile)
            headers = reader.fieldnames or []
            for row in reader:
                rows.append(dict(row))
        return rows, headers

    def write_csv_from_matrix(
        self,
        file_path: str,
        values_matrix: List[List[str]],
        save_as_new: bool = True
    ) -> str:
        """
        Write a matrix to a CSV file.

        Args:
            file_path: Original file path
            values_matrix: Data to write
            save_as_new: Whether to save as a new file with timestamp

        Returns:
            Path to the written file
        """
        if save_as_new:
            dir_path = os.path.dirname(file_path)
            filename = os.path.basename(file_path)
            timestamp = time.strftime("%a_%d%b_%Y_%Hh%Mm%Ss", time.localtime())
            file_path = os.path.join(dir_path, f"Modified_{timestamp}_{filename}")

        with open(file_path, "w", newline="", encoding=self.encoding) as csvfile:
            writer = csv.DictWriter(csvfile, values_matrix[0])
            writer.writeheader()
            writer.writerows(values_matrix[1:])

        return file_path

    def write_csv_from_dict_list(
        self,
        file_path: str,
        rows: List[Dict[str, Any]],
        headers: List[str]
    ):
        """
        Write a list of dictionaries to a CSV file.

        Args:
            file_path: Path to write to
            rows: List of row dictionaries
            headers: Column headers
        """
        with open(file_path, "w", newline="", encoding=self.encoding) as csvfile:
            writer = csv.DictWriter(csvfile, headers)
            writer.writeheader()
            writer.writerows(rows)

    def read_label_keys_file(
        self,
        file_path: str
    ) -> tuple[Dict[str, Dict[str, str]], List[str]]:
        """
        Read a FormLabelKeys CSV file.

        Args:
            file_path: Path to the CSV file

        Returns:
            Tuple of (dictionary keyed by label_key, list of headers)
        """
        label_keys_dict = {}
        headers = []

        with open(file_path, newline="", encoding=self.encoding) as csvfile:
            reader = csv.DictReader(csvfile)
            headers = reader.fieldnames or []
            for row in reader:
                label_key = row.get("label_key", "")
                if label_key:
                    label_keys_dict[label_key] = dict(row)

        return label_keys_dict, headers

    def read_country_list(self, file_path: str) -> List[str]:
        """
        Read a country list CSV file.

        Args:
            file_path: Path to the CSV file

        Returns:
            List of 3-character country codes
        """
        countries = []
        with open(file_path, newline="", encoding=self.encoding) as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row:
                    first_cell = row[0]
                    if first_cell and len(first_cell) == 3:
                        countries.append(first_cell)
        return countries

    def extract_languages_from_picklist_csv(
        self,
        file_path: str
    ) -> List[str]:
        """
        Extract language codes from picklist CSV headers.

        Args:
            file_path: Path to the CSV file

        Returns:
            List of language codes
        """
        languages = []
        with open(file_path, newline="", encoding=self.encoding) as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader, [])

            for header in headers:
                if header.startswith("values.label."):
                    lang = header.replace("values.label.", "")
                    if lang not in ["defaultValue", "localized", "en_DEBUG"]:
                        languages.append(lang)

        return languages

    def get_picklist_id_column_index(self, headers: List[str]) -> int:
        """Get the index of the picklist ID column."""
        try:
            return headers.index("id")
        except ValueError:
            return 1  # Default to second column

    def generate_ready_to_import_path(
        self,
        save_dir: str,
        prefix: str = "ReadyToImport"
    ) -> str:
        """
        Generate a path for a ready-to-import file.

        Args:
            save_dir: Directory to save in
            prefix: Filename prefix

        Returns:
            Full file path
        """
        return os.path.join(save_dir, f"{prefix}_FormLabelKeys.csv")
