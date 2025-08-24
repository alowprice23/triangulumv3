"""
agents/meta_agent.py
────────────────────
A lightweight self-improvement governor that sits above the three
role-agents (Observer, Analyst, Verifier).
"""

from __future__ import annotations

import math
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Deque, Dict, Optional

from agents.specialized_agents import ObserverAgent, AnalystAgent, VerifierAgent

# hyper-params for learning windows
WINDOW = 20                   # how many bugs constitute “recent history”
TEMP_STEP = 0.05              # temperature delta per adjustment
TOK_STEP = 128                # max_tokens delta
SUCCESS_TARGET = 0.90         # desired success-rate


@dataclass(slots=True)
class _HistoryEntry:
    ts: float
    success: bool
    tokens: int


@dataclass(slots=True)
class MetaAgent:
    """
    Holds references to the live AutoGen agents so it can mutate their
    run-time config *in place*.
    """

    observer: ObserverAgent
    analyst: AnalystAgent
    verifier: VerifierAgent
    optimiser_cb: Optional[Callable[[Dict], None]] = None

    _hist: Deque[_HistoryEntry] = field(default_factory=lambda: deque(maxlen=WINDOW))
    _bugs_seen: int = 0

    def record_result(self, bug_id: str, *, success: bool, tokens_used: int) -> None:
        """Call once per bug when Verifier declares final verdict."""
        self._hist.append(
            _HistoryEntry(ts=time.time(), success=success, tokens=tokens_used)
        )
        self._bugs_seen += 1

    def maybe_update(self) -> None:
        """
        If we have enough history, adjust LLM configs and push metric
        to optimiser.  Called from Scheduler/ParallelExecutor after each bug.
        """
        if len(self._hist) < WINDOW:
            return

        succ_rate = sum(1 for h in self._hist if h.success) / len(self._hist)
        mean_tok = sum(h.tokens for h in self._hist) / len(self._hist)

        error = SUCCESS_TARGET - succ_rate
        temp_delta = math.copysign(TEMP_STEP, error) if abs(error) > 0.05 else 0.0

        tok_delta = -TOK_STEP if mean_tok > 1800 else TOK_STEP if mean_tok < 800 else 0

        for agent in (self.observer, self.analyst, self.verifier):
            cfg = agent.llm_config["config_list"][0]
            new_temp = float(cfg.get("temperature", 0.1)) + temp_delta
            cfg["temperature"] = float(max(0.0, min(new_temp, 1.0)))

            new_max = int(cfg.get("max_tokens", 2048) + tok_delta)
            cfg["max_tokens"] = max(512, min(new_max, 4096))

        if self.optimiser_cb:
            self.optimiser_cb(
                {
                    "bugs_seen": self._bugs_seen,
                    "success_rate": round(succ_rate, 3),
                    "mean_tokens": int(mean_tok),
                    "temp_delta": temp_delta,
                    "tok_delta": tok_delta,
                }
            )

        for _ in range(WINDOW // 2):
            try:
                self._hist.popleft()
            except IndexError:
                break
