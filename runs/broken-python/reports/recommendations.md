# Recommendation Report — https://github.com/martinpeck/broken-python

_Generated: 2026-06-19T05:14:32.927202+00:00_

# Refactoring Recommendations — `polygons_polygons_polygon`

## Decision Posture

I'm accepting the upstream analysis's core judgment: **one structural locus, two corroborating signals**, severity unconfirmed. My recommendations are therefore **staged by evidence-gating** — cheap diagnostics first, irreversible structural changes last and only if justified. I will not recommend decomposition work before the blast radius is known, because that risks expensive refactoring against a `[low]`-severity trivial node.

---

## Ordered Recommendations

### R1 — Instrument before touching (diagnostic gate)
**Action:** Pull the three numbers the analysis flagged as missing: fan-in count, total graph node count, and the orphaned-component size on node removal.
**Justification:** Every downstream recommendation's value depends entirely on these. A SPOF separating 5% of a graph is a backlog note; one separating 40% is an incident waiting to happen. **Do no structural work until this gate is passed.**
**Cost:** Low. **Reversible:** N/A (read-only).
**Stop condition:** If blast radius < ~10% of graph AND alternate paths exist → downgrade to "monitor," stop here.

### R2 — Verify the SPOF is real (cheapest disconfirmation)
**Action:** Search for redundant/alternate paths bypassing the node.
**Justification:** An articulation point *by definition* has no bypass. If one exists, the detector's topology claim is stale or wrong, and the entire Rank-1 risk evaporates. This is the single cheapest way to *kill* the most severe finding — so it runs early. Disconfirmation is more valuable than confirmation here.
**Cost:** Low. **Reversible:** N/A.

### R3 — Introduce a redundant path (availability fix) — *conditional on R1 + R2*
**Action:** If R1 shows material blast radius and R2 confirms no bypass exists, add an alternate dependency route so the node is no longer an articulation point.
**Justification:** This directly converts the *binary, certain* availability risk into a non-issue. It is the highest-leverage fix because it targets the **topological fact**, not the gradient symptom. Critically, it's often **lower-cost than decomposition** — you may resolve the SPOF without redesigning the node at all.
**Cost:** Medium. **Reversible:** Yes (path can be removed).
**Why before R4:** Availability risk (binary) outranks maintainability risk (gradient), consistent with the upstream ranking.

### R4 — Decompose the god node (responsibility split) — *conditional on cohesion check*
**Action:** Only if fan-in reflects **mixed/unrelated responsibilities**, split the node along responsibility seams. If fan-in reflects a *legitimate shared utility*, do **not** decompose.
**Justification:** The God Node is a gradient symptom that overlaps with the SPOF. Decomposing a legitimately-shared utility adds complexity for no gain and may *create* new coupling. This is the most expensive and least reversible action, so it ranks last and carries the strictest gate.
**Cost:** High. **Reversible:** Poor (structural redesign).

---

## Sequencing Rationale (summary)

| Order | Action | Gate | Risk targeted |
|---|---|---|---|
| R1 | Quantify blast radius | none | (decision quality) |
| R2 | Disprove SPOF | none | kills R1 cheaply |
| R3 | Add redundant path | R1 material + R2 confirms | availability (binary) |
| R4 | Decompose | mixed responsibilities only | maintainability (gradient) |

**Guiding principle:** cheap disconfirmation → availability → maintainability. Two of four recommendations are *gates that can halt the work*, by design.

---

## Where I'd Revise This

- If R1 reveals **high fan-in but trivial blast radius** (node is a leaf-ish hub, not a cut vertex), R3 becomes moot and R4 becomes the primary lever.
- If the two smells turn out to be **independent** (contrary to the coupling assumption), R4's cohesion gate needs separate centrality data and may rank higher.
- I'm treating the `[low]` tags as **unverified, not trustworthy**. If you can share R1's numbers, I'll commit to a firm fix/monitor call instead of this conditional ladder.

Share the fan-in, total node count, and partition size and I'll collapse these conditionals into a definitive plan.

| # | Severity | Smell | Node | Evidence | Recommendation |
|---|---|---|---|---|---|
| 1 | low | god_node | polygons_polygons_polygon | centrality=0.2667, fan_in=2, fan_out=2 | Split polygons_polygons_polygon into cohesive sub-modules; invert high-traffic dependencies. |
| 2 | low | spof | polygons_polygons_polygon | fan_in=2, is_articulation=True | Introduce a seam so dependents don't all route through polygons_polygons_polygon. |

## Rationale
1. **polygons_polygons_polygon** — High centrality / fan-in: a structural single point of failure.
2. **polygons_polygons_polygon** — Articulation point with high fan-in: its removal disconnects the graph.