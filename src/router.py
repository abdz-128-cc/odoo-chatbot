from __future__ import annotations
from typing import Dict
from .prompts import render_router
import re, json

KEYWORDS_ONBOARDING = [
    "onboard","onboarding","new hire","first day","orientation",
    "equipment","laptop","account","provision","provisioning","setup",
    "vpn","email setup","joining","day 1","paperwork","access","badge"
]

def rule_based_route(question: str) -> str | None:
    q = question.lower()
    if any(k in q for k in KEYWORDS_ONBOARDING):
        return "onboarding"
    return None

def llm_route(llm, router_prompts: Dict[str, str], question: str, role: str):
    system, user = render_router(router_prompts["system"], router_prompts["user"],
                                 question=question, role=role)
    payload = f"{system}\n\n{user}"
    res = llm.complete_json(payload)
    route = res.get("route", "hr_policy")
    conf = float(res.get("confidence", 0.0))
    reason = res.get("reason", "n/a")
    return {"route": route if route in {"hr_policy","onboarding"} else "hr_policy",
            "confidence": conf, "reason": reason, "raw": res}

def choose_route(llm, router_prompts: Dict[str, str], question: str, role: str) -> str:
    rb = rule_based_route(question)
    if rb: return rb
    out = llm_route(llm, router_prompts, question, role)
    return out["route"]
