# Token-Efficiency Comparison — find_root_cause_and_fix_target_bug

| Metric | Baseline (raw code) | Graph-guided |
|---|---|---|
| Input tokens | 746 | 308 |
| Output tokens | 1842 | 978 |
| Total tokens | 2588 | 1286 |
| USD | 0.0000 | 0.0000 |
| Files read | 5 | 2 |
| Units read | 116 | 35 |
| Iterations | 1 | 1 |
| Time to root cause (s) | 31.625 | 19.562 |
| Root cause found | True | True |
| Tests green | True | True |

**Token savings (graph-guided vs baseline): 50.3%** — meets the >=40% target.

> Reported honestly per the brief: the figure is the measured token reduction on the same task; a small or negative result is shown as-is and reflects the target repo size and any agent overhead.