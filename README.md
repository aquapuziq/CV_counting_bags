# CV_counting_bags
A web application for processing conveyor video and automatically counting passing bags


## 1. Features

- Bag detection with **MMDetection / RTMDet-tiny**
- Fine-tuned one-class detector (`bag`)
- Conveyor ROI filtering
- Custom IoU-based object tracker
- Directional line-crossing counter
- Reverse crossing correction
- Conveyor anomaly monitoring:
  - `conveyor stopped`
  - `conveyor reverse`
- Annotated output video
- Asynchronous background processing with **Celery**
- **Redis** as Celery broker/result backend
- **SQLite** for persistent job state and anomaly records
- **FastAPI** REST API
- Swagger/OpenAPI documentation
- Persistent host-mounted `data/` directory

---

## 2. Architecture and Responsibilities


The application is divided into three main runtime components: **FastAPI**, **Redis**, and a **Celery worker**. FastAPI is responsible only for the HTTP layer: it accepts uploaded videos, stores them in persistent storage, creates a processing job in SQLite, and submits a background task to Celery. The request is then completed immediately with a `job_id`, so the HTTP connection does not wait for MMDetection inference to finish. Redis is used as the message broker between FastAPI and Celery. The Celery worker runs independently from the API process, loads the MMDetection model once, executes the full CV pipeline, writes the processed video, and saves the final bag count and detected anomalies to SQLite. Both the API and worker use the same mounted `data/` directory, so uploaded videos, processed videos, and the SQLite database remain available after Docker containers are recreated.

**FastAPI**
- accepts uploaded videos;
- stores source files in persistent storage;
- creates a processing job;
- sends the job to Celery;
- immediately returns a `job_id`;
- exposes status and download endpoints.

**Redis**
- acts as the Celery message broker;
- stores Celery task-result metadata.

**Celery worker**
- loads the MMDetection model;
- processes video in the background;
- updates job state;
- stores final bag count and anomalies;
- writes the processed video.

**SQLite**
- stores job status and metadata;
- stores detected anomaly intervals;
- remains persistent through the mounted `data/` directory.

---

## 3. Asynchronous Processing

Video inference is intentionally **not executed inside the HTTP request**.

The request workflow is:

```text
POST /jobs --> save uploaded video --> create Job(status = pending) -->
--> send Celery task to Redis --> immediately return HTTP 202 + job_id
```

The Celery worker then performs:

```text
pending --> processing (load input video --> run MMDetection -->
--> tracking + counting + anomaly monitoring --> write output video --> save result) --> done
```

If an exception occurs:

```text
processing --> failed
```

and the error message is stored in the database.

This satisfies the requirement that long-running inference must not block the HTTP request.

---
## 4. Anomaly Monitoring

Two conveyor-state anomalies are implemented.

### `conveyor stopped`

The system estimates object motion from recent track-center history.

A track is classified as stationary when its displacement over a temporal window is below the configured movement threshold.

A conveyor stop is activated only after the stationary condition persists for a confirmation period. This helps suppress false triggers caused by detector-box jitter.

### `conveyor reverse`

A normal conveyor direction vector is defined from the scene geometry.

For each track, displacement is projected onto this direction:

```text
projection > 0  # forward movement
projection < 0  # reverse movement
```

The reverse state is activated only after reverse movement persists for the configured confirmation duration.

### State persistence

Each anomaly stores:

- type;
- start time;
- end time.
(also start and end frames)

While an anomaly is active, it is displayed on the processed video.

### Important limitation

The conveyor state is inferred indirectly from tracked bag motion.

If there are no valid tracked bags in the ROI, the system cannot reliably determine whether the conveyor itself is moving.

---

## 5. Main Engineering Decisions

### RTMDet-tiny instead of a larger detector

My PC uses a laptop-class NVIDIA GPU with limited VRAM (4GB).

RTMDet-tiny provides a useful trade-off between:

- inference speed;
- GPU memory usage;
- detection accuracy.

Fine-tuning on the target scene produced sufficiently stable detections for tracking and counting.

### Simple IoU tracking

The tracking solution was intentionally kept simple because the scene is:

- fixed-camera;
- low-overlap;
- low-density;
- detector-stable.

This reduces unnecessary dependencies and makes the behavior easy to inspect and explain.

### Directional line counting

Counting line crossings rather than detections provides:

- protection from repeated frame-by-frame counting;
- clear business logic;
- explicit handling of conveyor reverse motion.

### Celery + Redis

Video inference is long-running and GPU-bound.

Moving processing into a Celery worker:

- prevents blocking HTTP requests;
- cleanly separates API and inference;
- allows queued processing jobs;
- makes failure handling explicit.

### SQLite

For a single-node test application, SQLite is sufficient and avoids introducing an unnecessary database service.

It persists:

- job states;
- result metadata;
- anomaly records.

### Persistent host directory

Using:

```yaml
./data:/app/data
```

makes file persistence explicit and easy to inspect.

It also directly satisfies the requirement that videos survive container recreation.

---

## Running the Application

### 1. Clone the repository

```bash
git clone https://github.com/aquapuziq/CV_counting_bags.git
cd CV_counting_bags
```

### 2. Build and start the application

```bash
docker compose up --build
```

Docker Compose starts:

- Redis;
- FastAPI;
- Celery worker.

### 3. Open Swagger UI

Open:

```text
http://localhost:8000/docs
```

---
## Processing the Provided Test Video

The test-assignment video is:

```text
input.mp4
```

To process it:

1. Open `http://localhost:8000/docs`.
2. Open `POST /jobs`.
3. Select `input.mp4`.
4. Execute the request.
5. Copy the returned `job_id`.
6. Call:

```http
GET /jobs/{job_id}
```

7. Poll until:

```json
{
  "status": "DONE"
}
```

8. Download the processed video using:

```http
GET /jobs/{job_id}/download
```

The same result is also available in:

```text
data/output/
```

---
## Technology Stack

| Component | Technology |
|---|---|
| API | FastAPI |
| Background processing | Celery |
| Message broker | Redis |
| Database | SQLite / SQLAlchemy |
| Detection | MMDetection |
| Detector | RTMDet-tiny |
| Tracking | Custom IoU tracker |
| Video processing | OpenCV |
| Deep learning | PyTorch |
| Containerization | Docker / Docker Compose |
| GPU runtime | NVIDIA CUDA |
