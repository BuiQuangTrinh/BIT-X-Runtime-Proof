"""
BIT-Audit v0.1 Demo

Runs a simple Tokens/Joule audit using sample compute runs.

Author: Bùi Quang Trịnh (Vietnam)
Framework: Boundary Information Theory (BIT)
"""

from bit_audit_v01 import AuditSample, BITAuditV01


def main():
    samples = [
        AuditSample(
            run_id="baseline_run",
            tokens_generated=1200,
            runtime_seconds=60,
            avg_power_watts=320,
        ),
        AuditSample(
            run_id="optimized_run",
            tokens_generated=1200,
            runtime_seconds=45,
            avg_power_watts=260,
        ),
        AuditSample(
            run_id="noisy_run",
            tokens_generated=400,
            runtime_seconds=70,
            avg_power_watts=330,
        ),
    ]

    auditor = BITAuditV01(low_efficiency_threshold=0.05)
    results = auditor.audit_many(samples)

    print("BIT-Audit v0.1 Demo")
    print("=" * 50)

    for result in results:
        print("\nRun ID:", result.run_id)
        print("Tokens generated:", result.tokens_generated)
        print("Runtime seconds:", result.runtime_seconds)
        print("Average power watts:", result.avg_power_watts)
        print("Energy joules:", result.energy_joules)
        print("Tokens/Joule:", result.tokens_per_joule)
        print("Joules/Token:", result.joules_per_token)
        print("Status:", result.efficiency_status)

    baseline = results[0]
    optimized = results[1]

    improvement = (
        (optimized.tokens_per_joule - baseline.tokens_per_joule)
        / baseline.tokens_per_joule
    ) * 100

    print("\nEfficiency Comparison")
    print("=" * 50)
    print("Baseline Tokens/Joule:", baseline.tokens_per_joule)
    print("Optimized Tokens/Joule:", optimized.tokens_per_joule)
    print("Estimated improvement:", f"{round(improvement, 2)}%")


if __name__ == "__main__":
    main()
