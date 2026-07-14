---
title: "Pipeline Management TODOs"
tags: ["todo", "planning"]
created_at: "2026-07-14"
last_updated_at: "2026-07-14"
---

# Pipeline Management TODOs

This document serves as a planning backlog for upcoming features and architectural decisions related to Pipeline Management.

### Schema Evolution Handling
- [ ] Determine the mechanism and user flow for handling upstream schema drift.
- [ ] Define how to alert the user when a Bronze data source inherently changes (e.g., the external API adds or drops a column).
- [ ] Design the propagation logic for how these structural changes alert and validate through the dependent Silver and Gold DAG nodes without silently breaking the pipeline.
