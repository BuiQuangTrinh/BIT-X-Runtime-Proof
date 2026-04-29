"""
BIT-Audit v0.1
A lightweight Tokens/Joule efficiency monitor.

Author: Bùi Quang Trịnh (Vietnam)
Framework: Boundary Information Theory (BIT)

Purpose:
This script estimates compute efficiency using simple operational metrics:
- tokens generated
- energy consumed
- runtime duration
- average power draw

Core idea:
A system is not efficient because it uses more power.
It is efficient when more useful tokens are produced per joule.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class AuditSample:
    run_id: str
    tokens_generated: int
    runtime_seconds: float
    avg_power_watts: float


@dataclass
class AuditResult:
    run_id: str
    tokens_generated: int
    runtime_seconds: float
    avg_power_watts: float
    energy_joules: float
    tokens_per_joule: float
    joules_per_token: float
    efficiency_status: str


class BITAuditV01:
    """
    Lightweight compute audit tool.

    BIT-Audit v0.1 does not control GPU hardware.
    It only calculates useful efficiency indicators from runtime logs.
    """

    def __init__(self, low_efficiency_threshold: float = 0.5):
        """
        low_efficiency_threshold:
        Minimum acceptable Tokens/Joule before the run is flagged.
        """
        self.low_efficiency_threshold = low_efficiency_threshold

    def audit(self, sample: AuditSample) -> AuditResult:
        if sample.runtime_seconds <= 0:
            raise ValueError("runtime_seconds must be greater than 0.")

        if sample.avg_power_watts <= 0:
            raise ValueError("avg_power_watts must be greater than 0.")

        if sample.tokens_generated < 0:
            raise ValueError("tokens_generated cannot be negative.")

        energy_joules = sample.avg_power_watts * sample.runtime_seconds

        if energy_joules == 0:
            tokens_per_joule = 0.0
            joules_per_token = 0.0
        else:
            tokens_per_joule = sample.tokens_generated / energy_joules
            joules_per_token = (
                energy_joules / sample.tokens_generated
                if sample.tokens_generated > 0
                else float("inf")
            )

        efficiency_status = (
            "OK"
            if tokens_per_joule >= self.low_efficiency_threshold
            else "LOW_EFFICIENCY"
        )

        return AuditResult(
            run_id=sample.run_id,
            tokens_generated=sample.tokens_generated,
            runtime_seconds=sample.runtime_seconds,
            avg_power_watts=sample.avg_power_watts,
            energy_joules=round(energy_joules, 3),
            tokens_per_joule=round(tokens_per_joule, 6),
            joules_per_token=round(joules_per_token, 6)
            if joules_per_token != float("inf")
            else float("inf"),
            efficiency_status=efficiency_status,
        )

    def audit_many(self, samples: List[AuditSample]) -> List[AuditResult]:
        return [self.audit(sample) for sample in samples]


if __name__ == "__main__":
    samples = [
        AuditSample(
            run_id="baseline_run_001",
            tokens_generated=1200,
            runtime_seconds=60,
            avg_power_watts=320,
        ),
        AuditSample(
            run_id="optimized_run_001",
            tokens_generated=1200,
            runtime_seconds=45,
            avg_power_watts=260,
        ),
        AuditSample(
            run_id="noisy_run_001",
            tokens_generated=400,
            runtime_seconds=70,
            avg_power_watts=330,
        ),
    ]

    auditor = BITAuditV01(low_efficiency_threshold=0.05)
    results = auditor.audit_many(samples)

    print("BIT-Audit v0.1")
    print("=" * 50)

    for result in results:
        print("\nRun ID:", result.run_id)
        print("Tokens:", result.tokens_generated)
        print("Runtime seconds:", result.runtime_seconds)
        print("Average power watts:", result.avg_power_watts)
        print("Energy joules:", result.energy_joules)
        print("Tokens/Joule:", result.tokens_per_joule)
        print("Joules/Token:", result.joules_per_token)
        print("Status:", result.efficiency_status)
