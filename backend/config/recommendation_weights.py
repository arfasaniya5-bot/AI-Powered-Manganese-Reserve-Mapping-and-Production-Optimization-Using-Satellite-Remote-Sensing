"""
Recommendation Engine Configuration
------------------------------------
Defines configurable weights, thresholds, and retrieval parameters
for the Case-Based Reasoning (CBR) recommendation engine.
"""

from typing import Dict

# Configurable similarity weights reflecting priority tiers (sum to 1.0)
SIMILARITY_WEIGHTS: Dict[str, float] = {
    "problem_cause": 0.20,        # Primary cause category & problem context
    "equipment_component": 0.20,  # Equipment type, component failed, failure mode
    "production": 0.20,           # Production shortfall %, planned/actual tonnage, risk level
    "weather": 0.12,              # Temperature, precipitation, wind speed, soil moisture
    "drilling_geology": 0.12,     # Rock type, transition zone, rotation pressure variance
    "mine_context": 0.08,         # Specific mine site matching
    "downtime_severity": 0.08,    # Downtime hours, maintenance type, failure severity
}

# Number of most-similar prototype cases to retrieve
DEFAULT_TOP_K: int = 5

# Minimum similarity threshold to qualify as a sufficiently similar case
# If top similarity score < MIN_SIMILARITY_THRESHOLD, triggers Part B.9 fallback
MIN_SIMILARITY_THRESHOLD: float = 0.35

# Progressive action status definitions
ACTION_STATUSES = [
    "PENDING",
    "IN_PROGRESS",
    "COMPLETED",
    "SUCCESSFUL",
    "UNSUCCESSFUL",
    "ESCALATED"
]
