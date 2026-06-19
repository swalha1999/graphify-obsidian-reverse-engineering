# Graph Report - /tmp/gstage/code  (2026-06-19)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 19 nodes · 15 edges · 6 communities
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 3|Community 3]]

## God Nodes (most connected - your core abstractions)
1. `Polygon` - 4 edges
2. `calc_polygon_details()` - 2 edges
3. `# TODO: find a better way to work this stuff out` - 1 edges
4. `# TODO: perhaps I should use the class Polygon instead!` - 1 edges
5. `# TODO: make this work for any type of polygon` - 1 edges

## Surprising Connections (you probably didn't know these)
- None detected - all connections are within the same source files.

## Import Cycles
- None detected.

## Communities (6 total, 0 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.40
Nodes (3): # TODO: find a better way to work this stuff out, # TODO: perhaps I should use the class Polygon instead!, # TODO: make this work for any type of polygon

### Community 3 - "Community 3"
Cohesion: 0.50
Nodes (3): Object, calc_polygon_details(), Polygon

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Polygon` connect `Community 3` to `Community 0`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **What connects `# TODO: find a better way to work this stuff out`, `# TODO: perhaps I should use the class Polygon instead!`, `# TODO: make this work for any type of polygon` to the rest of the system?**
  _3 weakly-connected nodes found - possible documentation gaps or missing edges._