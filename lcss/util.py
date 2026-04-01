from pathlib import Path
from typing import SupportsIndex

class ResourceBundleError(Exception):
    def __init__(self, file_path: Path | str | None = None) -> None:
        self.file = file_path

class ColorText(str):
    def replace(self, old: str, new: str, count: SupportsIndex = -1) -> "ColorText":
        return ColorText(super().replace(old, new, count))
