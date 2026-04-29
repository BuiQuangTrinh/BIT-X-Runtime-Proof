"""
BIT-X4 Demo Runtime
Runs a simple selective-computation demo using the BIT-X4 gate.

Author: Bùi Quang Trịnh (Vietnam)
Framework: Boundary Information Theory (BIT)
"""

from bit_x4_gate import BITX4Gate


def expensive_computation(text: str) -> str:
    """
    Placeholder for a costly AI/GPU operation.

    In a real system, this could be:
    - LLM inference
    - embedding generation
    - retrieval
    - GPU batch processing
    - simulation
    """
    return f"Processed: {text}"


def main():
    gate = BITX4Gate(threshold=0.55)

    inputs = [
        "Summarize GPU inference efficiency using Tokens per Joule.",
        "??? !!! asdf asdf",
        "Explain boundary-aware selective computation in one paragraph.",
        "",
        "Run a structured diagnosis of system instability from noisy input logs.",
    ]

    executed = 0
    skipped = 0

    print("BIT-X4 Runtime Demo")
    print("=" * 40)

    for item in inputs:
        result = gate.evaluate(item)

        print("\nInput:", repr(item))
        print("Coherence:", result.coherence_score)
        print("Decision:", result.decision)
        print("Reason:", result.reason)

        if result.decision == "EXECUTE":
            executed += 1
            output = expensive_computation(item)
            print("Output:", output)
        else:
            skipped += 1
            print("Output: skipped or deferred")

    total = executed + skipped

    print("\nSummary")
    print("=" * 40)
    print("Total inputs:", total)
    print("Executed:", executed)
    print("Skipped/deferred:", skipped)
    print("Estimated compute saved:", f"{round((skipped / total) * 100, 2)}%")


if __name__ == "__main__":
    main()
