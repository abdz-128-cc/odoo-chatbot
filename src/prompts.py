from __future__ import annotations
from string import Template

def render_prompt(tpl: str, **kwargs) -> str:
    # We support both {var} and $var styles; prefer {var}
    return tpl.format(**kwargs)

def render_router(system_tpl: str, user_tpl: str, **kwargs):
    return render_prompt(system_tpl, **kwargs), render_prompt(user_tpl, **kwargs)
