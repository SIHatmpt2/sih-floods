"""
Generic pipeline orchestration utilities.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

LOGGER = logging.getLogger(__name__)


def run_steps(
    data: Any,
    steps: list[
        tuple[str, Callable[[Any], Any]]
    ],
) -> Any:
    """
    Execute a sequence of named processing steps.

    Parameters
    ----------
    data:
        Initial input object.

    steps:
        List of tuples:

            ("step_name", callable)

    Returns
    -------
    Any
        Result returned by the final processing step.

    Raises
    ------
    Exception
        Re-raises any exception from a processing step after logging it.
    """
    result = data

    for step_name, function in steps:
        LOGGER.info(
            "Starting processing step: %s",
            step_name,
        )

        try:
            result = function(result)

        except Exception:
            LOGGER.exception(
                "Processing step failed: %s",
                step_name,
            )
            raise

        try:
            row_count = len(result)
        except TypeError:
            row_count = "n/a"

        LOGGER.info(
            "Completed processing step: %s | rows=%s",
            step_name,
            row_count,
        )

    return result
