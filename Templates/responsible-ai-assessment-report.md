# Responsible AI Assessment Report

> Standard output format for the **Responsible AI** companion agent. Rubric:
> `Protocols/RESPONSIBLE-AI-PROTOCOL.md`. Fill every field; keep observations
> separate from hypotheses; cite evidence for every finding. Advisory and
> simulation-only — this report never certifies or authorizes.

---

## 1. Header

| Field | Value |
|---|---|
| Subject | `<system / model / agent name>` |
| Assessed by | Responsible AI · rubric RESPONSIBLE-AI-PROTOCOL.md |
| Date (UTC) | `<yyyy-mm-dd hh:mm>` |
| Mode | assessment (simulation-only) |
| Inputs provided | model card ☐ · intended use ☐ · fairness metrics ☐ · safety/red-team ☐ · privacy/security ☐ · accessibility ☐ · transparency ☐ · oversight ☐ |
| RAI version | `<RAI-YYYY.MM>` |

---

## 2. Posture

> **`RAI-PASS` \| `RAI-WARN` \| `RAI-BLOCK`** — score **`<0–100>`** ·
> coverage **`<0–1>`** · confidence **`<HIGH\|MEDIUM\|LOW>`**

One-paragraph justification citing the deciding findings and any §8 override.
State explicitly: *a RAI-PASS is not a certification or compliance approval — it
means no high-confidence, high-impact Responsible AI gap was found within the
provided inputs.*

---

## 3. Pillar scores

| ID | Pillar | Maturity (0–4) | Tested | Evidence |
|---|---|---:|:---:|---|
| RAI-01 | Fairness and non-discrimination | | | |
| RAI-02 | Reliability and safety | | | |
| RAI-03 | Privacy and security | | | |
| RAI-04 | Inclusiveness and accessibility | | | |
| RAI-05 | Transparency and interpretability | | | |
| RAI-06 | Accountability and human oversight | | | |

---

## 4. Coverage note

Which inputs were and weren't available, and how missing evidence lowered
coverage and confidence (per rubric §6). List any pillar with no evidence.

---

## 5. Findings

> One block per finding, ordered by severity (Critical → Info). Every
> observation cites its evidence source and quote.

```
[<id>] <short title>
  Pillar       : RAI-0n <pillar name>
  Severity     : <Critical|High|Medium|Low|Info>
  Observation  : <what was seen>  (evidence: <source> "<quote>")
  Hypothesis   : <potential harm / why it matters>
  Remediation  : <concrete minimal action>
```

---

## 6. Top remediations, ranked

1. `<highest-impact action>` — addresses `[id(s)]`.
2. `<next>` — …
3. `<next>` — …

---

## 7. Attestation

- Advisory, simulation-only assessment; the subject system was **not** modified,
  certified, or authorized.
- Findings are AI-generated and may be inaccurate. Treat `RAI-WARN` /
  `RAI-BLOCK` as a trigger for human Responsible AI review, not certification.
- Based on public Responsible AI principles only; no internal or confidential
  content was used. The system's human owner remains accountable.
