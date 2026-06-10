# Readme for Elite Dangerous Quick Implementation Test

## 1. Process

### 1.1 Download large file from source url. 

- Define directory location for downloads
- Begin download stream
- Generate checksum as stream progresses
- On download completion, generate second checksum with same streaming process.
- Compare checksums for validation
- Generate and write manifest data on file (status, passed-checksum, is-valid, downloaded-at, source-uri, etc)

### 1.2 Evaluate incoming data composition and Determine Schemas

#### 1.2.1 Evaluate Original Data Structure

- Take sample of downloaded data
- Extract and determine original format and data schema (json, csv, etc)
- Write expected original format schema (e.g. json) template

#### 1.2.2 Determine Processes Data Structures and Schemas

- Evaluate sample and extracted original format schema (e.g. json)
- Determine normalization and relational structures
- Write Processed Schema(s) for normalized relational data

#### 1.2.3 Cleanup

- Update manifest file with relevant information - including location of schemas associated with downloaded data

### 1.3 Human-in-the-Loop Evaluation

- User must verify schema before implementation

### 1.4 Transfer and Loading of Data

#### 1.4.1 Preparation

- Ensure the data exists and is validated (via checksum process - indicated in manifest)
- Ensure schema(s) exist and are valid and human-approved
- Review data size and estimate number of entries
- Estimate time to complete process (transform and load into database (or other data storage)

#### 1.4.2. Execution

- Spin-up database
- Begin streaming process
- Inject data into database following normalization and schema(s)
- Update user on progress

#### 1.4.3. Cleanup

- Close all streams
- Update manifest
- Perform any database actions required for cleanup

## 2. Infrastructure

- Code: Python
- Database: Postgre

## 3. Issues & Recommendations

### 3.1 Checksum Redundancy
In section 1.1, generating a second checksum after download is thorough but doubles IO time for large files. If the stream checksum matches the expected hash, a second read-back is typically only needed if disk-write integrity is a specific concern.

### 3.2 Memory Management
When handling "large files," use chunked processing (e.g., Pandas `chunksize`) or native streaming. Avoid loading entire files into memory to prevent system crashes during schema evaluation or transformation.

### 3.3 Database Scaling
Standard `INSERT` statements are inefficient for high-volume injection into PostgreSQL. Use `COPY` commands or Pandas `to_sql` with `method='multi'` for significantly better performance.

## 4. Operational Security

### 4.1 Service User Provisioning
This application is designed to run as a dedicated, non-privileged service user (`elite_data_user`). User creation is an **Infrastructure** task and should be handled by an administrator.

To provision the necessary OS and Database users, run the following command once:
```bash
sudo .scripts/setup_users.sh
```

### 4.2 Permission Expectations
The application expects the `data/` directory to be writable by the current OS user. In production, ensure the directory is owned by the service user and has permissions set to `750`.
