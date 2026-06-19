# Token-Efficiency Comparison — find_root_cause_and_fix_target_bug

| Metric | Baseline (raw code) | Graph-guided |
|---|---|---|
| Input tokens | 203 | 45224 |
| Output tokens | 1212 | 518 |
| Total tokens | 1415 | 45742 |
| USD | 0.0000 | 0.0000 |
| Files read | 1 | 2 |
| Units read | 31 | 1660 |
| Iterations | 1 | 1 |
| Time to root cause (s) | 17.1569 | 12.5973 |
| Root cause found | True | True |
| Tests green | True | True |

**Token savings (graph-guided vs baseline): -3132.7%** — no token savings (graph-guided used at least as many tokens).

> Reported honestly per the brief: the figure is the measured token reduction on the same task; a small or negative result is shown as-is and reflects the target repo size and any agent overhead.