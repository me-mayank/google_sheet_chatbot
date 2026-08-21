import pytest
from datetime import date
from app.services.document_processor import process_document
from app.core.exceptions import EmptyDocumentError

def test_process_document_markdown():
    raw_text = """
# ICPC 2026

## Current Status
Teams: 3
Focus: DP

## 21 August 2026
### Contest
Contest #1 conducted.
### Results
Team A - 4 solved
"""
    doc = process_document(raw_text)
    assert doc.current_status == {"Teams": "3", "Focus": "DP"}
    assert len(doc.day_sections) == 1
    
    day1 = doc.day_sections[0]
    assert day1.date == date(2026, 8, 21)
    assert day1.raw_date_label == "21 August 2026"
    assert len(day1.subsections) == 2
    
    assert day1.subsections[0].title == "Contest"
    assert day1.subsections[0].content == "Contest #1 conducted."
    
    assert day1.subsections[1].title == "Results"
    assert day1.subsections[1].content == "Team A - 4 solved"

def test_process_document_heuristic():
    raw_text = """
21 August 2026

Contest
Contest #1 conducted.

Results
Team A - 4 solved
"""
    doc = process_document(raw_text)
    assert doc.current_status is None
    assert len(doc.day_sections) == 1
    
    day1 = doc.day_sections[0]
    assert day1.date == date(2026, 8, 21)
    assert day1.raw_date_label == "21 August 2026"
    assert len(day1.subsections) == 2
    
    assert day1.subsections[0].title.lower() == "contest"
    assert day1.subsections[1].title.lower() == "results"

def test_process_document_empty():
    raw_text = "Just some random text\\nwith no dates or sections."
    with pytest.raises(EmptyDocumentError):
        process_document(raw_text)
