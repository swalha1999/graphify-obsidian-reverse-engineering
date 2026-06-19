# Token-Efficiency Comparison — find_root_cause_and_fix_target_bug

| Metric | Baseline (raw code) | Graph-guided |
|---|---|---|
| Input tokens | 2514 | 553 |
| Output tokens | 1027 | 379 |
| Total tokens | 3541 | 932 |
| USD | 0.0000 | 0.0000 |
| Files read | 5 | 2 |
| Units read | 460 | 45 |
| Iterations | 1 | 1 |
| Time to root cause (s) | 18.3378 | 7.42775 |
| Root cause found | True | True |
| Tests green | True | True |

**Token savings (graph-guided vs baseline): 73.7%** — meets the >=40% target.

> Reported honestly per the brief: the figure is the measured token reduction on the same task; a small or negative result is shown as-is and reflects the target repo size and any agent overhead.