---
title: "Spansh Dataset Schema & Data Pedigree"
tags: ["spansh", "edmc", "eddn", "reference", "data-sources"]
created_at: "2026-07-09"
last_updated_at: "2026-07-09"
---

# Spansh Dataset Reference

This document provides a reference breakdown of the Spansh dataset dumps, the structure of the differential files, and the pedigree of the crowdsourced data feeding the pipeline.

## 1. Schema Categories & Duplication

The Spansh daily data dumps are categorized into three distinct architectural schemas. It is critical to understand that data is intentionally duplicated across these files to reduce bandwidth for different use cases.

*   **Factions (`factions.json.gz`):** 
    *   **Content:** Contains purely political and faction-based data, including influence levels, active states (e.g., War, Boom), and controlling systems.
*   **Galaxy (`galaxy.json.gz` - ~106 GB):** 
    *   **Content:** The master dataset. It contains the absolute entirety of the known galaxy. This includes every system, and nested within each system, every planet, moon, ring, station, and active fleet carrier.
    *   **Usage:** Only download this to bootstrap an empty database.
*   **Systems (`systems.json.gz` - ~5.7 GB):** 
    *   **Content:** A severely stripped-down subset of the Galaxy file. It contains ONLY top-level system metadata (XYZ coordinates, primary star class, system name, procedural generation seeds). 
    *   **Usage:** Used when bodies and stations are irrelevant to the algorithmic objective (e.g., pure distance routing).

## 2. Differential Dumps (Time Deltas)

To prevent developers from downloading 106 GB daily, Spansh provides time-filtered differential dumps (e.g., `galaxy_1day.json.gz`, `systems_1week.json.gz`). 

*   **Mechanism:** These files contain *only* the objects where an internal data attribute was updated within the specified time window.
*   **ETL Strategy:** 
    1.  Ingest the master file once to establish the base warehouse.
    2.  Schedule daily pipeline executions targeting the `_1day.json.gz` endpoint.
    3.  Execute an `UPSERT` (Update or Insert) command in the database to overwrite stale records with the 24-hour delta.

## 3. Data Pedigree: EDMC and EDDN

The data provided by Spansh is not pulled directly from Frontier Developments' servers. It is crowdsourced.

### The Ingestion Chain
1.  **Player Client:** A player jumps into a system.
2.  **EDMC (Elite Dangerous Market Connector) / EDDiscovery:** A third-party client running on the player's PC reads the local player journal logs.
3.  **EDDN (Elite Dangerous Data Network):** The client transmits the journal data to the central EDDN relay.
4.  **Spansh Database:** Spansh listens to the EDDN firehose, aggregates the events, and updates its master database.
5.  **Our Pipeline:** Our ETL pipeline periodically fetches the generated dumps from Spansh.

### Fidelity and Staleness Implications
Because the data relies entirely on physical player visitation, **fidelity is highly variable**.
*   If a system has not been visited by a player running an EDDN-enabled client in three years, the market data, faction states, and fleet carrier presences for that system in our database are frozen from three years ago.
*   **Design Rule:** Algorithmic pathing or search utilities querying the Gold layer must treat this data as "Last Known Good State", not absolute real-time truth. Queries evaluating volatile data (like markets) must actively filter or weight against the `updated_at` timestamps provided in the schema.
