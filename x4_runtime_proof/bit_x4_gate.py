"""
BIT-X4 Runtime Gate
Boundary-aware selective computation on existing systems.

Author: Bùi Quang Trịnh (Vietnam)
Framework: Boundary Information Theory (BIT)

Core idea:
Not all inputs deserve full computation.
This script evaluates input coherence before execution.
"""

from dataclasses import dataclass


@dataclass
class GateResult:
    input_text: str
    coherence_score: float
    decision: str
    reason: str


class BITX4Gate:
    """
    A lightweight boundary-aware gate.

    The gate estimates whether an input is coherent enough
    to justify full computation.
    """

    def __init__(self, threshold: float = 0.55):
        self.threshold = threshold

    def coherence_score(self, text: str) -> float:
        """
        Estimate input coherence using simple observable proxies.

        This is not a final scientific metric.
        It is a minimal runtime proof for selective execution.
        """

        if not text or not text.strip():
            return 0.0

        words = text.split()
        word_count = len(words)

        unique_ratio = len(set(words)) / max(word_count, 1)
        length_score = min(word_count / 20, 1.0)
        punctuation_penalty = min(
            sum(text.count(p) for p in ["!!!", "???", "..."]) * 0.1,
            0.3,
        )

        score = (0.45 * unique_ratio) + (0.55 * length_score) - punctuation_penalty

        return max(0.0, min(score, 1.0))

    def evaluate(self, text: str) -> GateResult:
        score = self.coherence_score(text)

        if score >= self.threshold:
            return GateResult(
                input_text=text,
                coherence_score=round(score, 3),
                decision="EXECUTE",
                reason="Input boundary is coherent enough for full computation.",
            )

        return GateResult(
            input_text=text,
            coherence_score=round(score, 3),
            decision="SKIP_OR_DEFER",
            reason="Input boundary is too weak or noisy for full computation.",
        )


if __name__ == "__main__":
    gate = BITX4Gate(threshold=0.55)

    samples = [
        "Summarize the energy efficiency of GPU inference using Tokens per Joule.",
        "asdf asdf ??? !!!",
        "",
        "Explain how boundary-aware selective computation can reduce wasted runtime.",
    ]

    for sample in samples:
        result = gate.evaluate(sample)
        print(result)
