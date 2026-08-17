CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS pulse_events (
  id TEXT PRIMARY KEY,
  category TEXT NOT NULL CHECK (category IN ('earthquake', 'wildfire', 'flood', 'storm', 'volcano')),
  severity TEXT NOT NULL CHECK (severity IN ('critical', 'warning', 'advisory', 'normal')),
  title TEXT NOT NULL,
  location TEXT NOT NULL,
  lat DOUBLE PRECISION NOT NULL CHECK (lat BETWEEN -90 AND 90),
  lon DOUBLE PRECISION NOT NULL CHECK (lon BETWEEN -180 AND 180),
  magnitude DOUBLE PRECISION,
  timestamp TIMESTAMPTZ NOT NULL,
  source TEXT NOT NULL,
  source_url TEXT,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  geom geometry(Point, 4326) NOT NULL,
  ai_summary TEXT,
  ai_category TEXT CHECK (ai_category IS NULL OR ai_category IN ('earthquake', 'wildfire', 'flood', 'storm', 'volcano')),
  ai_severity TEXT CHECK (ai_severity IS NULL OR ai_severity IN ('critical', 'warning', 'advisory', 'normal')),
  ai_confidence DOUBLE PRECISION CHECK (ai_confidence IS NULL OR ai_confidence BETWEEN 0 AND 1),
  ai_tags TEXT[] NOT NULL DEFAULT '{}',
  ai_rationale TEXT,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS pulse_events_geom_gix ON pulse_events USING GIST (geom);
CREATE INDEX IF NOT EXISTS pulse_events_timestamp_idx ON pulse_events (timestamp DESC);
CREATE INDEX IF NOT EXISTS pulse_events_source_idx ON pulse_events (source);
CREATE INDEX IF NOT EXISTS pulse_events_category_severity_idx ON pulse_events (category, severity);
CREATE INDEX IF NOT EXISTS pulse_events_metadata_gin ON pulse_events USING GIN (metadata);

CREATE TABLE IF NOT EXISTS ai_enrichment_jobs (
  id BIGSERIAL PRIMARY KEY,
  event_id TEXT NOT NULL REFERENCES pulse_events(id) ON DELETE CASCADE,
  status TEXT NOT NULL CHECK (status IN ('queued', 'running', 'completed', 'failed')),
  model TEXT,
  attempts INTEGER NOT NULL DEFAULT 0,
  error TEXT,
  requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ai_enrichment_jobs_status_idx ON ai_enrichment_jobs (status, requested_at);
