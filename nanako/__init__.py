"""
Nanako (ななこ) - An educational programming language for the generative AI era.

A Turing-complete language using minimal operations to teach programming fundamentals
through constrained computation with Japanese syntax.
"""

from .nanako import (
    NanakoRuntime,
    NanakoParser,
    NanakoArray,
    NanakoError,
)

# Import nanako_cli to register cell magic
try:
    from . import nanako_cli
except ImportError:
    pass

__version__ = "0.2.0"
__author__ = "Nanako Project"
__description__ = "An educational programming language for the generative AI era"

__all__ = [
    'NanakoRuntime',
    'NanakoParser', 
    'NanakoError',
    'NanakoArray',
]