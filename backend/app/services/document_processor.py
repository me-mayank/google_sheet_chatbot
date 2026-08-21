import hashlib
import re
from datetime import datetime, timezone
from dateutil import parser as date_parser

from app.models.document import ParsedDocument, DaySection, Subsection
from app.core.exceptions import EmptyDocumentError

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
    
    has_valid_sections = False

    def save_subsection():
        nonlocal current_sub_title, current_sub_content, current_subsections, current_status
        if current_sub_title:
            content = "\n".join(current_sub_content).strip()
            if current_sub_title.lower() == "current status":
                current_status = {}
                for line in content.split("\n"):
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

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_sub_title:
                current_sub_content.append(line)
            continue
            
        # 1. Try Date parsing first
        clean_date_str = re.sub(r"^(#+)?\s*(date:)?\s*", "", stripped, flags=re.IGNORECASE).strip()
        parsed_d = _parse_date(clean_date_str) if 4 < len(clean_date_str) < 30 else None
        
        if parsed_d:
            save_day_section()
            current_date = parsed_d
            current_date_label = clean_date_str
            has_valid_sections = True
            continue
            
        if clean_date_str.lower() == "current status":
            save_day_section()
            current_sub_title = clean_date_str
            has_valid_sections = True
            continue

        # 2. Check explicit Markdown headers for subsections
        if stripped.startswith("### ") or stripped.startswith("## ") or stripped.startswith("# "):
            header_title = re.sub(r"^#+\s*", "", stripped).strip()
            if len(header_title) < 60:
                save_subsection()
                current_sub_title = header_title
                has_valid_sections = True
                continue

        # 3. Heuristic Section Detection (if no markdown)
        if len(stripped) < 40 and stripped.lower() in SECTION_WHITELIST:
            save_subsection()
            current_sub_title = stripped
            has_valid_sections = True
            continue

        # 4. Regular content
        if not current_sub_title:
            current_sub_title = "General"
            
        current_sub_content.append(line)

    save_day_section()

    if not has_valid_sections and not current_status:
        raise EmptyDocumentError("No usable ICPC information was found in the document.")

    content_hash = hashlib.sha256(raw_text.encode('utf-8')).hexdigest()
    token_estimate = len(raw_text) // 4

    # If day_sections is empty but we have general notes, wrap them in a fallback date
    if not day_sections and current_subsections:
        day_sections.append(DaySection(
            date=datetime.now(timezone.utc).date(),
            raw_date_label="Current Notes",
            subsections=current_subsections
        ))

    return ParsedDocument(
        current_status=current_status,
        day_sections=day_sections,
        fetched_at=datetime.now(timezone.utc),
        content_hash=content_hash,
        token_estimate=token_estimate
    )
