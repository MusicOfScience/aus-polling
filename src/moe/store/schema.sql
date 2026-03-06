PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS raw_polls (
    raw_poll_id BIGINT PRIMARY KEY,
    source_name TEXT NOT NULL,
    source_file TEXT,
    payload JSON,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS clean_polls (
    clean_poll_id BIGINT PRIMARY KEY,
    raw_poll_id BIGINT,
    cleaned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    quality_flag TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS clean_normalized_polls (
    poll_id BIGINT PRIMARY KEY,
    clean_poll_id BIGINT,
    pollster TEXT NOT NULL,
    mode TEXT,
    fieldwork_start_date DATE,
    fieldwork_end_date DATE,
    sample_size INTEGER,
    region TEXT,
    question_type TEXT,
    methodology_notes TEXT,
    sponsor TEXT,
    source_link TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS features_polls (
    feature_id BIGINT PRIMARY KEY,
    poll_id BIGINT,
    feature_name TEXT NOT NULL,
    feature_value DOUBLE,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS model_outputs_polls (
    model_output_id BIGINT PRIMARY KEY,
    poll_id BIGINT,
    model_name TEXT NOT NULL,
    output_key TEXT NOT NULL,
    output_value DOUBLE,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS live_snapshots_polls (
    snapshot_id BIGINT PRIMARY KEY,
    snapshot_label TEXT NOT NULL,
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    region TEXT,
    payload JSON
);
