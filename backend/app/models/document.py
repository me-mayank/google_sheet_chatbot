from dataclasses import dataclass
from typing import Optional
from datetime import date, datetime

@dataclass
class Subsection:
    title: str
    content: str

@dataclass
class DaySection:
    date: date
    raw_date_label: str
    subsections: list[Subsection]

@dataclass
class ParsedDocument:
    current_status: Optional[dict]
    day_sections: list[DaySection]
    fetched_at: datetime
    content_hash: str
    token_estimate: int
