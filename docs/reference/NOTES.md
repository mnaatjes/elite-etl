# Notes for Project-wide Considerations

## Data Engineering Tools

### Tool Classifications

1. Basic & Prereqs

  - Interact with DB: Python, SQL
  - Excel
  - Libraries: Panda, NumPy, MatPlotLab


2. Big Data & Data Processing

  - Distributed Processing: Data into RDDs (Azure, AWS)
  - Big Data Tooling: Spark, PySpark, Scala (Hadoop, Hive depreciated)
  - Types: Batch and Streaming/Real-Time
  - Realtime Processing Tools: Kafka, Apache Flink

3. Orchestration

  - Happens during ETL/ELT 
  - Orchestration allows running of scripts during ETL/ELT Pipeline
  - Tooling: Apache Airflow, AWS (EC2, Lambda, AWS Glue), Azure (ADF), Google (GCS, DataFlow)

4. Data Warehouses & Data Lakehouses

  - Data can be Structured, Unstructured, Semi-Structured
  - Data Warehouse ONLY accepts Structured, Relational Data
  - Data Lakehouses accept ALL kinds of Data
  - Warehouse Tooling: BigQuery, RedShift, Azure, SynapseAnalytics, Snowflake
  - Lakehouse Tooling: DeltaLake, ApacheIceburg, DataBricks

5. Date Lineage

  - Tooling: OpenLineage + Marquez, DataHub, OpenMetadata, ApacheAtlas, DataBricks, dbtDocs

6. Dev Ops

  - Data Engineers expected to maintain Data Lifecycle
  - Model Deployment, CI/CD Pipelines, Automation
  - Tooling: Terraform, Docker, Kubernetes, AzureDevops, git

