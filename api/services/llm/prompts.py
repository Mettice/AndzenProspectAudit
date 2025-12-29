"""
Prompt templates for LLM-generated insights.

This module has been modularized. The main entry point is maintained here for backward compatibility.
All prompt functions are now in the prompts/ subdirectory.
"""
from .prompts import get_prompt_template

__all__ = ['get_prompt_template']
