"""Framework integrations for autolemetry."""

from .django import AutolemetryMiddleware as DjangoAutolemetryMiddleware
from .fastapi import AutolemetryMiddleware as FastAPIAutolemetryMiddleware
from .flask import init_autolemetry

__all__ = [
    "FastAPIAutolemetryMiddleware",
    "DjangoAutolemetryMiddleware",
    "init_autolemetry",
]
