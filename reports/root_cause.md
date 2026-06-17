# Root-Cause Analysis

Target: **[`andela/buggy-python`](https://github.com/andela/buggy-python)**.
Supports assignment §5.4 and TODO 6.4; feeds research question **RQ-5**.

How we found the bug, what the **root cause** was, and the steps that led us there —
plus a trace from each structural **finding** to its underlying cause.

---

## 1. The primary bug: mutable default argument in `foo()`

`snippets/foobar.py`:

```python
def foo(bar=[]):
    bar.append("baz")
    return bar
```

**Symptom.** Each call is expected to return `["baz"]`, but successive calls return
`["baz"]`, `["baz", "baz"]`, `["baz", "baz", "baz"]`, … — the list grows.

**Root cause.** Python evaluates a function's default arguments **once, at definition
time**, not on each call. So `bar=[]` creates *one* list that is shared by every call
that doesn't pass `bar`. Mutating it (`append`) persists across calls. (The module's own
docstring flags this: *"…default arguments… and how they can be misused."*)

**Fix.**

```python
def foo(bar=None):
    if bar is None:
        bar = []
    bar.append("baz")
    return bar
```

A fresh list per call — behaviour now correct and idempotent.

---

## 2. How the graph led us there (investigation path)

This is the point of the graph-guided approach — we did **not** read every file:

1. `graphify extract` → `artifacts/graph.json` (AST, free).
2. Metrics + smells ranked the nodes. `snippets_foobar_foo` (i.e. `foo()`) came back as
   **both** a God-Node candidate (centrality 0.30, fan-in 3) **and** a **SPOF**
   (articulation point) — see `reports/recommendations.md`.
3. The most-depended-on, structurally-central node is exactly where a defect is most
   damaging, so we **opened that node first** — and found the mutable-default bug.

The graph pointed at the right ~80 lines without dumping the whole repo into the model
(the token study, `reports/token_efficiency.md`, quantifies that: ~50% fewer tokens).

---

## 3. Each finding → its structural cause

| Finding (evidence) | Structural root cause |
|---|---|
| **God Node `snippets_io`** (centrality 0.40, fan-out 4) | The I/O module mixes file reading with computation; every calculation function (`calculate_paid_loans`, `calculate_unpaid_loans`, `average_paid_loans`) depends on it. No separation between I/O and logic → a coupling hub. |
| **God Node `snippets_foobar_foo`** (centrality 0.30, fan-in 3) | A shared helper that three call sites depend on, with no abstraction in between. |
| **SPOF `snippets_foobar_foo`** (articulation point, fan-in 3) | It is the *only* connector between its dependents — removing it disconnects the graph. There is no alternative path, so it is a single point of failure as well as a bug site. |

---

## 4. Secondary defects (same hub: `snippets/io.py`)

The most-coupled module is also riddled with line-level bugs — consistent with it being
the risk centre. Root causes, briefly:

| Code | Cause | Fix |
|---|---|---|
| `data("loans")` | dict accessed as a callable | `data["loans"]` |
| `loan.amount`, `loan.status` | dict items accessed as attributes | `loan["amount"]`, `loan["status"]` |
| `status !== "unpaid"` | JavaScript operator (SyntaxError) | `status != "unpaid"` |
| `loan.status is "paid"` | identity check for string equality | `== "paid"` |
| `sun(...)`, `length(...)` | typo / non-Python builtins | `sum(...)`, `len(...)` |

**Takeaway (RQ-5):** the structural analysis didn't just describe the architecture — it
pointed straight at the highest-risk node, where both the canonical Python bug *and* the
densest cluster of defects lived. Structure first, raw code second.
