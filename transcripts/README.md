# AI Tool Transcripts

This directory contains the full, unedited record of the AI pair programming session for the Northwind Group Take-Home Assignment (v2), as required by Section 5 of the evaluation instructions.

---

## Files in this Directory

1. **`transcript.jsonl`**:
   The complete raw JSONL event stream of the entire interaction session, containing every user prompt, assistant chain-of-thought reasoning, tool execution, terminal command output, and error correction.
2. **`transcript_full.jsonl`**:
   The full, untruncated JSONL stream with complete raw tool call payloads and reasoning blocks.

---

## Session Overview & Key Verification Interactions

- **Phase 1: Ingestion & Trap Spotting:**
  - Ingested all 15 source data files without modification.
  - Identified adversarial prompt injection attempt in `adjustments.json` (Entry `JE-006` with memo instructing reviewer to skip balance checks).
  - Detected mapping classification bug in `map_uk.csv` (local account 2310 *Deferred income* mapped to revenue 4100).
  - Detected missing closing exchange rate for `GBP/SGD` in `fx_rates.csv` and confirmed compliance with the strict `null` return policy.
  - Diagnosed intercompany timing discrepancy ($10,160 in-transit invoice `INV-US-2291`) and un-revalued USD monetary liability (£11,957.88 FX loss).
  - Verified India acquisition cutoff (filtering H2 post-acquisition results vs. Q1 pre-acquisition net assets).

- **Phase 2: Test-Driven Development & AI Mistake Corrections:**
  - Automated unit test suite built incrementally for validator, adjustments, FX engine, intercompany reconciler, and acquisition engine.
  - Caught 3 concrete AI tool mistakes documented in [`VALIDATION.md`](../docs/VALIDATION.md):
    1. AI initially proposed accepting CFO bypass in `JE-006` -> Fixed in commits `537f9e4` and `ec74cdc`.
    2. AI initially misattributed intercompany variance entirely to in-transit invoice and suggested plugging £11,957.88 -> Fixed in commit `35a4fe1`.
    3. AI initially attempted to estimate missing GBP/SGD closing rate -> Fixed in commit `843eccd`.

- **Phase 3: End-to-End Execution & Artifact Synthesis:**
  - Consolidated statement synthesis executed via single command `python main.py`.
  - Invariants verified: $\text{Assets} = \text{Liabilities} + \text{Equity}$ balanced to the penny.
  - 100% of required files written to `data/output/`.

