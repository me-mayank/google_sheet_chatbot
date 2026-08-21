import hashlib
import re
from datetime import datetime, timezone
from dateutil import parser as date_parser

from app.models.document import ParsedDocument, DaySection, Subsection
from app.core.exceptions import EmptyDocumentError

# Predefined section names for heuristic detection
SECTION_WHITELIST = {
    "contest", "results", "topics", "topics covered", "observations", 
    "important observations", "problems", "problems / issues", "decisions", 
    "next steps", "current status"
}

def _parse_date(date_str: str):
    try:
        return date_parser.parse(date_str).date()
    except (ValueError, OverflowError):
        return None

def process_document(raw_text: str) -> ParsedDocument:
    lines = raw_text.splitlines()
    
    current_status = None
    day_sections = []
    
    current_date = None
    current_date_label = None
    current_subsections = []
    
    current_sub_title = None
    current_sub_content = []

    def save_subsection():
        nonlocal current_sub_title, current_sub_content, current_subsections, current_status
        if current_sub_title:
            content = "\\n".join(current_sub_content).strip()
            if current_sub_title.lower() == "current status" and not current_date:
                # If we hit current status before any dates, parse it as a dict
                current_status = {}
                for line in content.split("\\n"):
                    if ":" in line:
                        k, v = line.split(":", 1)
                        if v.strip():
                            current_status[k.strip()] = v.strip()
            else:
                current_subsections.append(Subsection(title=current_sub_title, content=content))
        current_sub_title = None
        current_sub_content = []

    def save_day_section():
        nonlocal current_date, current_date_label, current_subsections
        save_subsection()
        if current_date and current_date_label:
            day_sections.append(DaySection(
                date=current_date,
                raw_date_label=current_date_label,
                subsections=current_subsections
            ))
        current_date = None
        current_date_label = None
        current_subsections = []

    # Simple heuristic to detect if a line is a date (standalone)
    date_regex = re.compile(r"^(\d{1,2}\s+[a-zA-Z]+\s+\d{4}|[a-zA-Z]+\s+\d{1,2},?\s+\d{4}|\d{4}-\d{2}-\d{2})$")

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_sub_title:
                current_sub_content.append(line)
            continue
            
        # Check Markdown H2 (## Date)
        if stripped.startswith("## "):
            possible_date = stripped[3:].strip()
            parsed_d = _parse_date(possible_date)
            if parsed_d:
                save_day_section()
                current_date = parsed_d
                current_date_label = possible_date
                continue
            elif possible_date.lower() == "current status":
                save_day_section()
                current_sub_title = possible_date
                continue

        # Check Markdown H3 (### Section)
        if stripped.startswith("### "):
            save_subsection()
            current_sub_title = stripped[4:].strip()
            continue
            
        # Check Markdown H1 (# Title)
        if stripped.startswith("# "):
            continue # Ignore main title for logic

        # Heuristic Date Detection (if no markdown)
        if date_regex.match(stripped):
            parsed_d = _parse_date(stripped)
            if parsed_d:
                save_day_section()
                current_date = parsed_d
                current_date_label = stripped
                continue
                
        # Heuristic Section Detection (if no markdown)
        if len(stripped) < 40 and stripped.lower() in SECTION_WHITELIST:
            save_subsection()
            current_sub_title = stripped
            continue

        # Regular content
        if current_sub_title:
            current_sub_content.append(line)

    save_day_section()

    if not day_sections and not current_status:
        raise EmptyDocumentError("No usable ICPC information was found in the document.")

    content_hash = hashlib.sha256(raw_text.encode('utf-8')).hexdigest()
    # Simple token estimate: roughly 4 chars per token
    token_estimate = len(raw_text) // 4

    return ParsedDocument(
        current_status=current_status,
        day_sections=day_sections,
        fetched_at=datetime.now(timezone.utc),
        content_hash=content_hash,
        token_estimate=token_estimate
    )
