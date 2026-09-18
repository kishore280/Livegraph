# LiveGraph — Backlog

From prior-art research (Graphiti, AGENTiGraph, Memgraph agent demo, react-force-graph):

- [ ] Fuzzy entity resolution (embedding-similarity match instead of exact-match-after-normalize) — kills duplicate nodes, biggest graph-quality win
- [ ] Mark stale facts instead of overwriting them — reuse existing timestamps, cheap "graph remembers what changed" narrative
- [ ] Stable-layout node-appear animation — switch graph panel to react-force-graph (d3-force), feed only new nodes/edges by stable id so physics keeps old node positions instead of full-relayout jump on each poll
- [ ] Push graph deltas over the existing SSE channel instead of polling `/subgraph` every 4s — reuse chat-streaming SSE plumbing, removes poll lag/jank
