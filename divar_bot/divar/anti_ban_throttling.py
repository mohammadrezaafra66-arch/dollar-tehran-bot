"""Adaptive anti-ban throttling engine.

This module reacts to operational risk signals such as captcha detections,
restriction pages, repeated failures, and elevated retry rates. The goal is to
slow down or temporarily pause unsafe workloads before large-scale failures
cascade through the runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class AntiBanSignals:
    """Operational signals collected during runtime."""

    captcha_events: int = 0
    restriction_events: int = 0
    extraction_failures: int = 0
    successful_extractions: int = 0
    proxy_failures: int = 0
    session_failures: int = 0


@dataclass(frozen=True)
class AntiBanDecision:
    """Adaptive throttling decision."""

    action: str
    timing_profile: str
    pause_seconds: int = 0
    reason: str = ""
    risk_score: float = 0.0


class AdaptiveAntiBanThrottler:
    """Converts operational signals into runtime throttling decisions."""

    def __init__(self) -> None:
        self._signals: Dict[str, AntiBanSignals] = {}

    def record_success(self, runtime_key: str) -> None:
        self._state(runtime_key).successful_extractions += 1

    def record_failure(self, runtime_key: str) -> None:
        self._state(runtime_key).extraction_failures += 1

    def record_captcha(self, runtime_key: str) -> None:
        self._state(runtime_key).captcha_events += 1

    def record_restriction(self, runtime_key: str) -> None:
        self._state(runtime_key).restriction_events += 1

    def record_proxy_failure(self, runtime_key: str) -> None:
        self._state(runtime_key).proxy_failures += 1

    def record_session_failure(self, runtime_key: str) -> None:
        self._state(runtime_key).session_failures += 1

    def decide(self, runtime_key: str) -> AntiBanDecision:
        """Return adaptive runtime throttling decision."""

        signals = self._state(runtime_key)

        total_attempts = max(1, signals.successful_extractions + signals.extraction_failures)
        failure_rate = signals.extraction_failures / total_attempts

        risk_score = 0.0
        risk_score += min(0.4, signals.captcha_events * 0.15)
        risk_score += min(0.3, signals.restriction_events * 0.12)
        risk_score += min(0.2, signals.proxy_failures * 0.05)
        risk_score += min(0.2, signals.session_failures * 0.05)
        risk_score += min(0.3, failure_rate * 0.5)

        if risk_score >= 0.85:
            return AntiBanDecision(
                action="pause_runtime",
                timing_profile="safe",
                pause_seconds=1800,
                reason="critical_risk_detected",
                risk_score=round(risk_score, 2),
            )

        if risk_score >= 0.6:
            return AntiBanDecision(
                action="slow_down",
                timing_profile="safe",
                pause_seconds=300,
                reason="elevated_risk_detected",
                risk_score=round(risk_score, 2),
            )

        if risk_score >= 0.35:
            return AntiBanDecision(
                action="reduce_parallelism",
                timing_profile="normal",
                pause_seconds=60,
                reason="moderate_risk_detected",
                risk_score=round(risk_score, 2),
            )

        return AntiBanDecision(
            action="continue",
            timing_profile="normal",
            reason="healthy_runtime",
            risk_score=round(risk_score, 2),
        )

    def snapshot(self, runtime_key: str) -> Dict[str, int]:
        """Return operational signal snapshot."""

        state = self._state(runtime_key)
        return {
            "captcha_events": state.captcha_events,
            "restriction_events": state.restriction_events,
            "extraction_failures": state.extraction_failures,
            "successful_extractions": state.successful_extractions,
            "proxy_failures": state.proxy_failures,
            "session_failures": state.session_failures,
        }

    def _state(self, runtime_key: str) -> AntiBanSignals:
        if runtime_key not in self._signals:
            self._signals[runtime_key] = AntiBanSignals()
        return self._signals[runtime_key]
