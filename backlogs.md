# LiveGraph — Backlog

From prior-art research (Graphiti, AGENTiGraph, Memgraph agent demo, react-force-graph):

- [ ] Fuzzy entity resolution (embedding-similarity match instead of exact-match-after-normalize) — kills duplicate nodes, biggest graph-quality win
- [ ] Mark stale facts instead of overwriting them — reuse existing timestamps, cheap "graph remembers what changed" narrative
- [x] Stable-layout node-appear animation — graph panel uses react-force-graph-2d (d3-force), keyed by stable id
- [ ] Push graph deltas over the existing SSE channel instead of polling `/subgraph` every 4s — reuse chat-streaming SSE plumbing, removes poll lag/jank
- [ ] Click a graph node to see its details (name, type, connected edges) in a side panel
