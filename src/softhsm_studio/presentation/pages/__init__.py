"""Modular pages for the HSM management console."""

from .dashboard import DashboardPage
from .objects import ObjectsPage
from .providers import ProvidersPage
from .sessions import SessionsPage
from .slots import SlotsPage

__all__ = ["DashboardPage", "ObjectsPage", "ProvidersPage", "SessionsPage", "SlotsPage"]
