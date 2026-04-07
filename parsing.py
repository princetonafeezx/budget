from __future__ import annotations 

import datetime
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

def parse_date(date_text: str) -> date:
    raw = date_text.strip()
    patterns = [ 
        "%Y-%m-%d", 
        "%m/%d/%Y", 
        "%m/%d/%y", 
        "%Y/%m/%d", 
        "%d/%m/%Y", 
        "%d/%m/%y", 
    ]
    for pattern in patterns: 
        try: 
            return datetime.strptime(raw, pattern).date()
        except ValueError: 
            continue 
    raise ValueError(f"Unsupported date format: {date_text}") 

def parse_amount(amount_text: str) -> float:
    original = (amount_text or "").strip() 
    cleaned = ( 
        original.replace("$", "") 
        .replace(",", "") 
        .replace("\xa0", "")
        .replace("\u202f", "")
        .strip()
        
    )