"""Evaluation engine for the FinServe BCM simulation."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple


class SimulationEngine:
    """Score BCM simulation outputs using structured, scenario-aware heuristics."""

    EXPECTED_DEPENDENCIES: Dict[str, List[str]] = {
        "mobile banking app": ["core banking api", "auth", "fraud detection engine"],
        "online transfer service": ["core banking api", "payment gateway"],
        "fraud detection engine": ["ml model server", "transaction db"],
        "core banking api": ["primary db", "message queue"],
    }

    EXPECTED_SERVICE_ORDER: List[str] = [
        "core banking api",
        "fraud detection engine",
        "mobile banking app",
        "online transfer service",
    ]

    def evaluate(self, final_plan: str, scenario: str) -> Dict[str, Any]:
        """Evaluate the crew output for BCM realism.

        Args:
            final_plan: Raw CrewAI final output.
            scenario: Scenario identifier supplied by the caller.

        Returns:
            A dictionary of detailed evaluation metrics and an overall score.
        """
        payload = self._parse_payload(final_plan)
        all_text = self._flatten_to_text(payload).lower()

        severity_score, severity_notes = self._score_severity(payload, all_text, scenario)
        dependency_score, dependency_notes = self._score_dependencies(payload, all_text)
        rto_rpo_score, rto_met, rpo_met, rto_rpo_notes = self._score_rto_rpo(payload, all_text)
        escalation_score, escalation_notes = self._score_escalation(payload, all_text)
        communication_score, communication_notes = self._score_communications(payload, all_text)
        ambiguity_score, ambiguity_notes = self._score_ambiguity(payload, all_text)
        structure_score, structure_notes = self._score_structure(payload)

        weighted_total = round(
            (
                severity_score * 0.18
                + dependency_score * 0.18
                + rto_rpo_score * 0.2
                + escalation_score * 0.14
                + communication_score * 0.16
                + ambiguity_score * 0.1
                + structure_score * 0.04
            ),
            1,
        )

        score = {
            "scenario": scenario,
            "parsed_output": isinstance(payload, dict),
            "severity_classification_score": severity_score,
            "dependency_recovery_score": dependency_score,
            "rto_rpo_adherence_score": rto_rpo_score,
            "escalation_quality_score": escalation_score,
            "communication_completeness_score": communication_score,
            "ambiguous_telemetry_handling_score": ambiguity_score,
            "structured_output_score": structure_score,
            "rto_met": rto_met,
            "rpo_met": rpo_met,
            "overall_kpi_score": weighted_total,
            "evaluation_notes": {
                "severity": severity_notes,
                "dependencies": dependency_notes,
                "rto_rpo": rto_rpo_notes,
                "escalation": escalation_notes,
                "communications": communication_notes,
                "ambiguity": ambiguity_notes,
                "structure": structure_notes,
            },
        }

        print("\n🔬 SIMULATION ENGINE EVALUATION:")
        for key, value in score.items():
            print(f"   {key}: {value}")
        return score

    def _parse_payload(self, final_plan: str) -> Any:
        """Parse crew output as JSON when possible, otherwise return raw text."""
        raw_text = str(final_plan).strip()
        if not raw_text:
            return {}

        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    return {"raw_output": raw_text}
            return {"raw_output": raw_text}

    def _flatten_to_text(self, payload: Any) -> str:
        """Flatten nested payload content into a searchable string."""
        if isinstance(payload, dict):
            return " ".join(f"{key} {self._flatten_to_text(value)}" for key, value in payload.items())
        if isinstance(payload, list):
            return " ".join(self._flatten_to_text(item) for item in payload)
        return str(payload)

    def _extract_services(self, payload: Any, text: str) -> List[str]:
        """Extract service mentions from structured data or free text."""
        candidates = set()
        if isinstance(payload, dict):
            for key in ("affected_services", "confirmed_impacted_services", "approved_recovery_priorities", "dependency_aware_recovery_sequence"):
                value = payload.get(key)
                if isinstance(value, list):
                    for item in value:
                        candidates.add(str(item).lower())
        for service in self.EXPECTED_DEPENDENCIES:
            if service in text:
                candidates.add(service)
        return sorted(candidates)

    def _score_severity(self, payload: Any, text: str, scenario: str) -> Tuple[int, List[str]]:
        """Score severity classification quality."""
        notes: List[str] = []
        score = 45

        severity_value = ""
        if isinstance(payload, dict):
            severity_value = str(payload.get("severity_classification", "")).lower()

        if any(word in severity_value for word in ("critical", "sev1", "sev-1", "major")):
            score += 30
            notes.append("Severity classification explicitly stated.")
        elif "critical" in text or "major" in text:
            score += 18
            notes.append("Severity implied in narrative text.")
        else:
            notes.append("Missing explicit severity classification.")

        if scenario == "ransomware" and any(word in text for word in ("ransomware", "encrypted", "data center")):
            score += 15
            notes.append("Scenario context reflected in severity reasoning.")
        elif scenario == "cloud_outage_ddos" and any(word in text for word in ("ddos", "cloud outage", "aws", "us-east-1")):
            score += 15
            notes.append("Scenario context reflected in severity reasoning.")
        else:
            notes.append("Severity rationale weakly tied to scenario.")

        if any(word in text for word in ("customer impact", "regulatory", "blast radius", "degraded", "down")):
            score += 10
            notes.append("Severity rationale considers operational/business impact.")

        return min(score, 100), notes

    def _score_dependencies(self, payload: Any, text: str) -> Tuple[int, List[str]]:
        """Score dependency-aware recovery sequencing."""
        notes: List[str] = []
        score = 35

        services = self._extract_services(payload, text)
        if services:
            score += 15
            notes.append(f"Identified services: {', '.join(services)}.")
        else:
            notes.append("No impacted services extracted.")

        dependency_mentions = 0
        for service, dependencies in self.EXPECTED_DEPENDENCIES.items():
            if service in text and any(dep in text for dep in dependencies):
                dependency_mentions += 1
        score += min(dependency_mentions * 10, 30)
        if dependency_mentions:
            notes.append(f"Dependency relationships referenced for {dependency_mentions} services.")
        else:
            notes.append("Little evidence of dependency mapping.")

        ordered_hits = [service for service in self.EXPECTED_SERVICE_ORDER if service in text]
        if len(ordered_hits) >= 2 and ordered_hits[:2] == self.EXPECTED_SERVICE_ORDER[:2]:
            score += 20
            notes.append("Recovery sequence starts with core dependencies before channels.")
        else:
            notes.append("Recovery order does not clearly prioritize foundational services first.")

        return min(score, 100), notes

    def _score_rto_rpo(self, payload: Any, text: str) -> Tuple[int, bool, bool, List[str]]:
        """Score stated adherence to RTO and RPO constraints."""
        notes: List[str] = []
        score = 30

        rto_met = any(phrase in text for phrase in ("within 4 hours", "rto met", "under 240 minutes"))
        rpo_met = any(phrase in text for phrase in ("15 minutes", "rpo", "replication lag")) and "rpo" in text or "15 minutes" in text

        if rto_met:
            score += 35
            notes.append("RTO commitment explicitly addressed.")
        else:
            notes.append("RTO commitment missing or unclear.")

        if rpo_met:
            score += 25
            notes.append("RPO commitment explicitly addressed.")
        else:
            notes.append("RPO commitment missing or unclear.")

        if any(term in text for term in ("verification", "health-check", "validated", "restored", "checkpoint")):
            score += 10
            notes.append("Recovery verification evidence included.")

        return min(score, 100), rto_met, rpo_met, notes

    def _score_escalation(self, payload: Any, text: str) -> Tuple[int, List[str]]:
        """Score escalation quality and human-in-the-loop handling."""
        notes: List[str] = []
        score = 30

        if any(term in text for term in ("pagerduty", "incident commander", "executive escalation", "human escalation", "on-call", "regulator")):
            score += 30
            notes.append("Escalation paths are clearly referenced.")
        else:
            notes.append("Escalation paths are weak or absent.")

        if any(term in text for term in ("decision", "approval", "command posture", "bridge", "war room")):
            score += 20
            notes.append("Command-and-control structure is visible.")

        if any(term in text for term in ("assumption", "bounded assumption", "awaiting clarification", "request clarification")):
            score += 20
            notes.append("Escalation logic distinguishes uncertainty from confirmed facts.")
        else:
            notes.append("Escalation handling does not clearly address uncertainty.")

        return min(score, 100), notes

    def _score_communications(self, payload: Any, text: str) -> Tuple[int, List[str]]:
        """Score completeness of stakeholder communications."""
        notes: List[str] = []
        score = 25

        required_labels = ["customer_notification", "executive_briefing", "regulator_update"]
        present = [label for label in required_labels if label in text]
        score += len(present) * 15
        if present:
            notes.append(f"Audience-specific communications present: {', '.join(present)}.")
        else:
            notes.append("Expected communication audiences not clearly present.")

        if any(term in text for term in ("delivery_tracking", "delivered", "status", "channel")):
            score += 15
            notes.append("Delivery tracking or channel status included.")

        if any(term in text for term in ("next update", "follow-up", "eta", "restoration time")):
            score += 15
            notes.append("Messages include next-step timing or commitments.")

        return min(score, 100), notes

    def _score_ambiguity(self, payload: Any, text: str) -> Tuple[int, List[str]]:
        """Score handling of ambiguous or degraded telemetry."""
        notes: List[str] = []
        score = 20

        if any(term in text for term in ("ambiguous", "uncertain", "telemetry gap", "contradictory", "incomplete")):
            score += 35
            notes.append("Ambiguous telemetry is explicitly acknowledged.")
        else:
            notes.append("Ambiguous telemetry not explicitly acknowledged.")

        if any(term in text for term in ("bounded assumption", "clarification", "human escalation", "manual validation", "awaiting logs")):
            score += 25
            notes.append("Response includes bounded assumptions or clarification path.")
        else:
            notes.append("No clear plan for resolving telemetry ambiguity.")

        if any(term in text for term in ("evidence", "log", "metric", "dashboard", "trace")):
            score += 20
            notes.append("Evidence-based reasoning is present.")

        return min(score, 100), notes

    def _score_structure(self, payload: Any) -> Tuple[int, List[str]]:
        """Score whether output is structured enough for reliable evaluation."""
        notes: List[str] = []
        if not isinstance(payload, dict):
            return 20, ["Output is not parseable as a structured JSON object."]

        expected_keys = {
            "incident_id",
            "overall_status_summary",
            "communications",
        }
        present = [key for key in expected_keys if key in payload]
        notes.append(f"Structured keys present: {', '.join(present) if present else 'none'}.")
        return min(40 + len(present) * 20, 100), notes