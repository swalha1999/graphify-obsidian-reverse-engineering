# Reverse-Engineered Architecture

## Overview

| Metric | Value |
|---|---|
| Modules | 5 |
| Classes | 0 |
| Functions | 6 |
| Dependencies | 9 (9 call) |

- **Most central:** `snippets_io` (0.40), `snippets_foobar_foo` (0.30), `snippets_foobar` (0.20)
- **Single points of failure (articulation points):** `snippets_foobar_foo`, `snippets_io`
- **Highest blast radius:** `snippets_foobar_foo` (3), `snippets_foobar` (1), `snippets_io_average_paid_loans` (1)
- **Dependency cycles:** none

## Block & Call Graph

```mermaid
flowchart LR
  main["main"]
  subgraph snippets_foobar["snippets_foobar"]
    snippets_foobar_foo["foo"]
  end
  snippets_init["snippets_init"]
  subgraph snippets_io["snippets_io"]
    snippets_io_average_paid_loans["average_paid_loans"]
    snippets_io_calculate_paid_loans["calculate_paid_loans"]
    snippets_io_calculate_unpaid_loans["calculate_unpaid_loans"]
    snippets_io_read_file["read_file"]
  end
  subgraph snippets_loop["snippets_loop"]
    snippets_loop_lambda_array["lambda_array"]
  end
  main --> snippets_foobar_foo
  snippets_foobar --> snippets_foobar_foo
  snippets_init --> snippets_foobar
  snippets_init --> snippets_foobar_foo
  snippets_io --> snippets_io_average_paid_loans
  snippets_io --> snippets_io_calculate_paid_loans
  snippets_io --> snippets_io_calculate_unpaid_loans
  snippets_io --> snippets_io_read_file
  snippets_loop --> snippets_loop_lambda_array
```

## OOP Class Map

_No classes found — this codebase is module/function-only._
