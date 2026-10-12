# Artifact Server

Simple HTTP server to receive build artifacts from Jenkins CI/CD pipeline.

## Features

- POST `/upload` - Upload artifacts (multipart/form-data)
- GET `/health` - Health check endpoint
- Token-based authentication (Bearer token)
- Validates project name, file extensions, and upload size
- Organizes artifacts by project and build number
- Atomic writes (temp file + rename)
- No external dependencies (stdlib only)

## Configuration (Environment Variables)

| Variable | Default | Description |
|----------|---------|-------------|
| `ARTIFACT_ROOT_DIR` | `D:/Builds` | Root directory for stored artifacts |
| `ARTIFACT_SERVER_TOKEN` | *required* | Bearer token for authentication |
| `MAX_UPLOAD_SIZE` | `104857600` (100MB) | Maximum upload size in bytes |
| `ARTIFACT_SERVER_HOST` | `0.0.0.0` | Bind address |
| `ARTIFACT_SERVER_PORT` | `8080` | Listen port |

## Running on Windows

```powershell
$env:ARTIFACT_ROOT_DIR = "D:\Builds"
$env:ARTIFACT_SERVER_TOKEN = "your-secure-token-here"
$env:ARTIFACT_SERVER_PORT = "8080"
python server.py
```

## Running on Linux/macOS

```bash
export ARTIFACT_ROOT_DIR="/var/builds"
export ARTIFACT_SERVER_TOKEN="your-secure-token-here"
export ARTIFACT_SERVER_PORT=8080
python3 server.py
```

## API

### POST /upload

Upload an artifact file.

**Headers:**
- `Authorization: Bearer <token>`
- `Content-Type: multipart/form-data`

**Form Fields:**
- `project` (string) - Project name (alphanumeric, dash, underscore only)
- `build_number` (string) - Build number / identifier
- `branch` (string, optional) - Git branch name
- `file` (file) - The artifact file
- `file_name` (string) - Original filename (sent as separate field)

**Response (201 Created):**
```json
{
  "status": "created",
  "project": "CppBuildLab",
  "build_number": "42",
  "file": "calculator_app",
  "size": 123456,
  "path": "CppBuildLab/42/calculator_app"
}
```

**Errors:**
- 400 - Invalid request (missing fields, bad project name, disallowed extension)
- 401 - Invalid or missing token
- 409 - File already exists
- 413 - Upload too large
- 500 - Server error

### GET /health

Health check endpoint.

**Response (200 OK):**
```json
{"status": "ok"}
```

## Security Notes

⚠️ **This server is for trusted local networks only.**

- No HTTPS/TLS - use a reverse proxy (nginx, Caddy) for production
- No rate limiting
- Token authentication only
- No audit logging beyond basic access logs
- Runs as single-threaded process

For any non-lab use, deploy behind a reverse proxy with TLS termination and proper authentication.

## Directory Structure

Artifacts are stored as:
```
<ARTIFACT_ROOT_DIR>/
  <project_name>/
    <build_number>/
      artifact_file1
      artifact_file2.xml
      ...
```

## Jenkins Integration

In Jenkins pipeline:
```groovy
environment {
    ARTIFACT_SERVER_URL = credentials('artifact-server-url')
    ARTIFACT_SERVER_TOKEN = credentials('artifact-server-token')
}

sh '''
curl -X POST \
  -H "Authorization: Bearer ${ARTIFACT_SERVER_TOKEN}" \
  -F "project=CppBuildLab" \
  -F "build_number=${BUILD_NUMBER}" \
  -F "branch=${BRANCH_NAME}" \
  -F "file=@build/calculator_app" \
  -F "file_name=calculator_app" \
  "${ARTIFACT_SERVER_URL}/upload"
'''
```

Store URL and token in Jenkins Credentials (Secret Text).