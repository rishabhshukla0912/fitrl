# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Data models for the Life Optimization Environment.

Actions and observations for a 7-day life optimization episode
with morning fitness, afternoon work, and evening recovery phases.
"""

from enum import Enum
from typing import Optional, Union

from openenv.core.env_server.types import Action, Observation
from pydantic import Field, field_validator, ConfigDict


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class WorkoutType(str, Enum):
    strength = "strength"
    cardio = "cardio"
    yoga = "yoga"
    rest = "rest"


class IntensityLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TaskType(str, Enum):
    email = "email"
    deep_work = "deep_work"
    support = "support"
    scheduling = "scheduling"
    rest = "rest"


class EffortLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


# ---------------------------------------------------------------------------
# Sub-action models
# ---------------------------------------------------------------------------

class FitnessAction(Action):
    """Morning fitness action."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "workout_type": "strength",
            "intensity": "medium",
            "duration": 30
        }
    })
    
    workout_type: WorkoutType = Field(..., description="Type of workout: strength, cardio, yoga, or rest")
    intensity: IntensityLevel = Field(..., description="Workout intensity: low, medium, or high")
    duration: int = Field(default=30, ge=0, le=120, description="Duration in minutes (0-120)")


class WorkAction(Action):
    """Afternoon work action."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "task_type": "deep_work",
            "effort_level": "medium"
        }
    })
    
    task_type: TaskType = Field(..., description="Type of work task: email, deep_work, support, scheduling, or rest")
    effort_level: EffortLevel = Field(..., description="Effort level for the task: low, medium, or high")


# ---------------------------------------------------------------------------
# Top-level action (one of fitness or work; evening needs neither)
# ---------------------------------------------------------------------------

class LifeOptimizationAction(Action):
    """Action for the Life Optimization environment.

    Supply fitness_action during morning, work_action during afternoon.
    Leave both None for evening recovery.
    """
    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "name": "Morning - Strength Training",
                "value": {
                    "fitness_action": {
                        "workout_type": "strength",
                        "intensity": "medium",
                        "duration": 35
                    }
                }
            },
            {
                "name": "Afternoon - Deep Work",
                "value": {
                    "work_action": {
                        "task_type": "deep_work",
                        "effort_level": "high"
                    }
                }
            },
            {
                "name": "Evening - Recovery (No action)",
                "value": {}
            }
        ]
    })
    
    fitness_action: Optional[FitnessAction] = Field(
        default=None,
        description="Morning fitness action (provide during morning phase only)"
    )
    work_action: Optional[WorkAction] = Field(
        default=None,
        description="Afternoon work action (provide during afternoon phase only)"
    )

    @field_validator("fitness_action", "work_action", mode="before")
    @classmethod
    def validate_actions(cls, v):
        """Reject string values and convert to None; only accept dicts or instances."""
        if isinstance(v, str):
            # If LLM returns a string instead of object, treat as None (use baseline)
            return None
        return v


# ---------------------------------------------------------------------------
# Observation
# ---------------------------------------------------------------------------

class LifeOptimizationObservation(Observation):
    """Observation from the Life Optimization environment."""

    day: int = Field(default=1, description="Current day (1-7)")
    time_of_day: str = Field(default="morning", description="morning | afternoon | evening")
    energy: float = Field(default=0.8, description="Energy level [0, 1]")
    fatigue: float = Field(default=0.1, description="Fatigue level [0, 1]")
    focus: float = Field(default=0.7, description="Focus level [0, 1]")
    soreness: float = Field(default=0.0, description="Muscle soreness [0, 1]")
    sleep_hours: float = Field(default=7.0, description="Last night sleep hours")
    last_workout: Optional[str] = Field(default=None, description="Last workout type")
    pending_tasks: int = Field(default=3, description="Number of pending tasks")
    consistency: float = Field(default=0.5, description="Routine consistency [0, 1]")
    productivity: float = Field(default=0.5, description="Productivity score [0, 1]")
    fitness_score: float = Field(default=0.5, description="Fitness score [0, 1]")
