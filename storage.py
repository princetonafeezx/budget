from __future__ import annotations

import csv
import json
import os
import uuid
import warnings
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, cast

from parsing import parse_amount
from schemas import CategorizedRecord

CATEGORIZED_FIELDS = [ 
    "date", 
    "merchant", 
    "amount", 
    "category", 
    "subcategory", 
    "confidence", 
    "match_type", 
]


