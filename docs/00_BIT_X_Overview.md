# BIT-X Overview

Author: Bùi Quang Trịnh (Vietnam)  
Framework: Boundary Information Theory (BIT)

---

## Purpose

BIT-X is the applied branch of Boundary Information Theory.

It translates the core BIT framework into practical system layers:

- boundary logic
- compute audit
- system diagnosis
- runtime proof

The goal is not only to describe systems, but to build testable tools that can measure, diagnose, and reduce unnecessary computation.

---

## Core Principle

> Not all information deserves equal computation.

Modern systems often compute, transfer, and react too much by default.

BIT-X starts from a different assumption:

A system should compute more only when the boundary condition justifies it.

---

## BIT-X Structure

### BIT-X1 — Boundary Logic

The conceptual layer.

BIT-X1 studies how life, natural systems, relationships, and organizations become stable through boundary formation, coherence, and low-noise information flow.

---

### BIT-X2 — Compute Audit

The operational layer.

BIT-X2 measures efficiency in compute systems using practical indicators such as:

- Tokens/Joule
- Joules/Token
- runtime duration
- average power draw
- useful output per unit of energy

This branch contains early audit scripts for estimating compute efficiency.

---

### BIT-X3 — System Diagnosis

The diagnostic layer.

BIT-X3 studies system instability through:

- structural failure
- operational failure
- phase mismatch
- noise overload
- boundary collapse

Its purpose is to help identify whether a system is failing because of design, execution, timing, or excessive noise.

---

### BIT-X4 — Runtime Proof

The execution layer.

BIT-X4 tests boundary-aware selective computation.

Instead of executing every input by default, the system first evaluates input coherence through a runtime gate.

Possible decisions:

- execute
- skip
- defer
- compress
- reroute

This branch contains early demo code for selective execution.

---

## Repository Map

```text
BIT-X-Runtime-Proof/
├── README.md
├── tài liệu/
├── tài sản/
├── logic ranh giới x1/
├── x2_compute_audit/
├── x3_system_diagnosis/
└── x4_runtime_proof/
