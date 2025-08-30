"""
Data models and structures for Google Sheets integration.
Contains all dataclasses, enums, and column mappings.
"""

from dataclasses import dataclass
from typing import List
from enum import Enum


# STEAM Topic Enumeration
class STEAMTopic(Enum):
    SCIENCE = "Science"
    TECHNOLOGY = "Technology" 
    ENGINEERING = "Engineering"
    ART = "Art"
    ANY = "ANY"  # Can handle any topic
    DO_NOT_ASSIGN = "DO NOT ASSIGN"  # Should not be assigned work


# PROJECT COLUMN MAPPINGS
@dataclass(frozen=True)
class ProjectColumns:
    # INFO
    PROJECT_ID: str =               "A"
    PROJECT_NAME: str =             "B"
    DESCRIPTION: str =              "C"
    PRIORITY: str =                 "D"
    WRITER_REQUIRED: str =          "E"  # was "WRITER?"
    DESIGNER_REQUIRED: str =        "F"  # was "DESIGNER?"
    READY_TO_ASSIGN: str =          "G"

    # WRITERS
    ASSIGNED_WRITER: str =          "I"
    DOCUMENT_LINK: str =            "J"
    WRITER_DEADLINE: str =          "K"
    WRITER_SEND_METHOD: str =       "L"

    # WRITER QC
    WRITER_QC_CONTROLLER: str =     "N"
    WRITER_QC_FORM_POST: str =      "O"
    WRITER_QC_REVISION_COUNT: str = "P"
    WRITER_QC_RESULT: str =         "Q"

    # DESIGNERS
    ASSIGNED_DESIGNER: str =        "S"
    MEDIA_LINK: str =               "T"
    DESIGN_DEADLINE: str =          "U"
    DESIGN_SEND_METHOD: str =       "V"

    # DESIGNER QC
    DESIGN_QC_CONTROLLER: str =     "X"
    DESIGN_QC_FORM_POST: str =      "Y"
    DESIGN_QC_REVISION_COUNT: str = "Z"
    DESIGN_QC_RESULT: str =         "AA"

    # METADATA
    PROJECT_START_DATE: str =       "AC"
    WRITER_TOPIC: str =             "AC"
    WRITER_DONE_DATE: str =         "AD"
    WRITER_QC_EXIT_DATE: str =      "AE"
    DESIGN_DONE_DATE: str =         "AF"
    DESIGN_QC_EXIT_DATE: str =      "AG"
    PROJECT_END_DATE: str =         "AH"


# DESIGNER DATA MODELS
@dataclass
class Designer:
    name:                   str
    platform:               str
    assigned_work:          List[str]
    designs_finished:       List[str]
    num_finished:           int
    quality_percent:        float
    avg_turnaround_time:    float
    kpi:                    float
    platform_rank:          int
    open_tasks:             int = 0
    score:                  float = 0.0


@dataclass(frozen=True)
class DesignerColumns:
    NAME: str =                 'A'
    PLATFORM: str =             'B'
    ASSIGNED_WORK: str =        'C'  # list of PIDs
    DESIGNS_FINISHED: str =     'D'  # list of PIDs
    NUM_FINISHED: str =         'E'  # count
    QUALITY_PERCENT: str =      'I'
    AVG_TURNAROUND_TIME: str =  'J'
    KPI: str =                  'K'
    DESIGN_PRINCIPLES: str =     'M' # YES / NO


# WRITER DATA MODELS
@dataclass
class Writer:
    name:                   str
    category:               str  # STEAM topic they specialize in
    assigned_work:          List[str]
    writings_finished:      List[str]
    num_finished:           int
    quality_percent:        float
    avg_turnaround_time:    float
    kpi:                    float
    topic_rank:             int  # Ranking based on topic match
    open_tasks:             int = 0
    score:                  float = 0.0


@dataclass(frozen=True)
class WriterColumns:
    NAME: str =                 'A'
    CATEGORY: str =             'B'  # STEAM topic specialization
    ASSIGNED_WORK: str =        'C'  # list of PIDs
    WRITINGS_FINISHED: str =    'D'  # list of completed PIDs
    NUM_FINISHED: str =         'E'  # count
    QUALITY_PERCENT: str =      'I'
    AVG_TURNAROUND_TIME: str =  'J'
    KPI: str =                  'K'


# Create singleton instances for use throughout the codebase
PROJECT_COLUMNS = ProjectColumns()
DESIGNER_COLUMNS = DesignerColumns()
WRITER_COLUMNS = WriterColumns()


# PLATFORM AND TOPIC HIERARCHIES
PLATFORM_HIERARCHY: List[str] = [
    "Adobe",        # TOP PICK
    "Figma",
    "Canva",
    "ProCreate",
    "Sketch",
    "Variety",
    "Other",        # LAST PICK
]

# Topic hierarchy for writer ranking (exact match gets highest priority)
TOPIC_HIERARCHY: dict[str, int] = {
    "Science": 0,
    "Technology": 1,
    "Engineering": 2,
    "Art": 3,
    "ANY": 4,  # Can do any topic, but lower priority than specialists
    "DO NOT ASSIGN": 999  # Should never be assigned
}
