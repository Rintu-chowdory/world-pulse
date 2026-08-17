# V0.3 / V0.4 integration research

## USGS

The USGS real-time feed page recommends real-time GeoJSON feeds for developer applications and exposes summary and detail feed options. The FDSN Event Web Service supports custom GeoJSON queries with `starttime`, `endtime`, `updatedafter`, magnitude, geographic, ordering, and limit parameters. The USGS documentation specifically recommends real-time GeoJSON feeds for display use cases because they provide better performance and availability than custom catalog queries.

Recommended implementation: poll the USGS `all_hour.geojson` feed every 60 seconds as the primary near-real-time source, use `all_day.geojson` for recovery/backfill, normalize the feature `id`, `properties.time`, `properties.mag`, `properties.place`, `geometry.coordinates`, and `properties.url`, and retain `updatedafter` query support for future backfill and reconciliation.

## NASA FIRMS

NASA FIRMS exposes area, country, data availability, map key, and related services. The active-fire API uses a free `MAP_KEY`; the documented transaction limit is 5,000 transactions per 10-minute interval. The area endpoint uses a path shape like `/api/area/csv/{MAP_KEY}/{SOURCE}/{AREA_COORDINATES}/{DAY_RANGE}` and returns CSV fields including latitude, longitude, acquisition date/time, satellite, instrument, confidence, FRP, scan, track, and day/night. A world-wide VIIRS request can return tens of thousands of rows per day, so the ingestion engine must bound the query window, deduplicate, batch, and avoid broadcasting every raw detection as an individual high-volume UI event.

Recommended implementation: poll a configurable FIRMS source such as `VIIRS_NOAA20_NRT` or `VIIRS_NOAA21_NRT` for `world/1` only when a key is configured, parse CSV with Python's standard library, group detections into coarse spatial cells, and emit representative fire clusters with count, maximum FRP, latest acquisition time, and confidence summary. Keep the raw detection count in metadata for later analytics.

## Live engine and deployment

World Pulse currently has a FastAPI API and a Next.js client. V0.4 should use a single in-process async ingestion supervisor for the first production iteration: USGS and FIRMS pollers run on independent intervals, a normalized in-memory event store serves HTTP reads, and a WebSocket hub broadcasts `event.upsert`, `event.remove`, and `heartbeat` messages. This is suitable for one Render API instance. If the service scales horizontally, move the event store and fan-out to Redis Streams or Pub/Sub and use a shared durable store.

## Sources

1. https://earthquake.usgs.gov/earthquakes/feed/
2. https://earthquake.usgs.gov/fdsnws/event/1/
3. https://firms.modaps.eosdis.nasa.gov/api/
4. https://firms.modaps.eosdis.nasa.gov/content/academy/data_api/firms_api_use.html
