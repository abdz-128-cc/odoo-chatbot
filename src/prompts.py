from __future__ import annotations
from string import Template

def render_prompt(tpl: str, **kwargs) -> str:
    """
    Renders a prompt template with keyword arguments.

    Args:
        tpl: The template string.
        **kwargs: Variables to substitute.

    Returns:
        The rendered prompt.
    """
    return tpl.format(**kwargs)

def render_router(system_tpl: str, user_tpl: str, **kwargs):
    """
    Renders system and user prompts for routing.

    Args:
        system_tpl: The system template.
        user_tpl: The user template.
        **kwargs: Variables to substitute.

    Returns:
        A tuple of rendered system and user prompts.
    """
    return render_prompt(system_tpl, **kwargs), render_prompt(user_tpl, **kwargs)
