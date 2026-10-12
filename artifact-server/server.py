#!/usr/bin/env python3
"""
Artifact Server for CppBuildLab
A simple HTTP server to receive build artifacts from Jenkins.

NOT FOR PRODUCTION USE - Lab environment only.
Use HTTPS and proper authentication for any non-trusted network.
"""

import os
import sys
import uuid
import tempfile
import shutil
import logging
import mimetypes
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class Config:
    def __init__(self):
        self.root_dir = Path(os.environ.get('ARTIFACT_ROOT_DIR', 'D:/Builds')).resolve()
        self.token = os.environ.get('ARTIFACT_SERVER_TOKEN', '')
        self.max_upload_size = int(os.environ.get('MAX_UPLOAD_SIZE', '104857600'))
        self.allowed_extensions = {'.exe', '.dll', '.so', '.a', '.xml', '.json', '.txt', '.log', ''}
        self.host = os.environ.get('ARTIFACT_SERVER_HOST', '0.0.0.0')
        self.port = int(os.environ.get('ARTIFACT_SERVER_PORT', '8080'))

    def validate(self) -> bool:
        if not self.token:
            logger.error("ARTIFACT_SERVER_TOKEN not set")
            return False
        try:
            self.root_dir.mkdir(parents=True, exist_ok=True)
            test_file = self.root_dir / '.write_test'
            test_file.write_text('test')
            test_file.unlink()
        except Exception as e:
            logger.error(f"Cannot write to root directory {self.root_dir}: {e}")
            return False
        return True


config = Config()


def sanitize_filename(filename: str) -> str:
    name = Path(filename).name
    name = name.replace('..', '').replace('/', '').replace('\\', '')
    if not name or name in ('.', '..'):
        name = f'file_{uuid.uuid4().hex[:8]}'
    return name


def validate_extension(filename: str) -> bool:
    ext = Path(filename).suffix.lower()
    return ext in config.allowed_extensions


def validate_project_name(name: str) -> bool:
    if not name or not name.strip():
        return False
    name = name.strip()
    if '..' in name or '/' in name or '\\' in name:
        return False
    if not all(c.isalnum() or c in '-_' for c in name):
        return False
    return True


def get_project_dir(project_name: str, build_number: str) -> Path:
    safe_project = sanitize_filename(project_name)
    safe_build = sanitize_filename(build_number)
    return config.root_dir / safe_project / safe_build


class ArtifactHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        logger.info("%s - %s", self.client_address[0], format % args)

    def _send_json(self, status: int, data: dict) -> None:
        import json
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _send_error(self, status: int, message: str) -> None:
        self._send_json(status, {'error': message})

    def _check_auth(self) -> bool:
        auth = self.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            self._send_error(401, 'Missing or invalid Authorization header')
            return False
        token = auth[7:]
        if token != config.token:
            logger.warning("Invalid token from %s", self.client_address[0])
            self._send_error(401, 'Invalid token')
            return False
        return True

    def _read_exact(self, length: int) -> bytes:
        data = bytearray()
        remaining = length
        while remaining > 0:
            chunk = self.rfile.read(min(remaining, 8192))
            if not chunk:
                break
            data.extend(chunk)
            remaining -= len(chunk)
        return bytes(data)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
        else:
            self._send_error(404, 'Not found')

    def do_POST(self) -> None:
        if not self._check_auth():
            return

        parsed = urlparse(self.path)
        if parsed.path != '/upload':
            self._send_error(404, 'Not found')
            return

        content_type = self.headers.get('Content-Type', '')
        if not content_type.startswith('multipart/form-data'):
            self._send_error(400, 'Content-Type must be multipart/form-data')
            return

        content_length = self.headers.get('Content-Length')
        if not content_length:
            self._send_error(411, 'Content-Length required')
            return

        total_size = int(content_length)
        if total_size > config.max_upload_size:
            self._send_error(413, f'Upload too large (max {config.max_upload_size} bytes)')
            return

        try:
            boundary = self._parse_boundary(content_type)
            if not boundary:
                self._send_error(400, 'Missing boundary')
                return

            fields = self._parse_multipart(boundary, total_size)
            project = fields.get('project', [''])[0]
            build_number = fields.get('build_number', [''])[0]
            branch = fields.get('branch', [''])[0]
            file_data = fields.get('file', [b''])[0]
            file_name = fields.get('file_name', [''])[0]
            multipart_filename = fields.get('file_filename', [''])[0]

            if not validate_project_name(project):
                self._send_error(400, 'Invalid project name')
                return

            if not build_number:
                self._send_error(400, 'Missing build_number')
                return

            if not file_name:
                file_name = multipart_filename
            if not file_name:
                self._send_error(400, 'Missing file_name')
                return

            safe_name = sanitize_filename(file_name)
            if not validate_extension(safe_name):
                self._send_error(400, f'Extension not allowed: {Path(safe_name).suffix}')
                return

            if len(file_data) == 0:
                self._send_error(400, 'Empty file')
                return

            project_dir = get_project_dir(project, build_number)
            project_dir.mkdir(parents=True, exist_ok=True)

            dest_path = project_dir / safe_name
            if dest_path.exists():
                self._send_error(409, f'File already exists: {safe_name}')
                return

            with tempfile.NamedTemporaryFile(dir=project_dir, delete=False) as tmp:
                tmp.write(file_data)
                tmp_path = Path(tmp.name)

            tmp_path.rename(dest_path)

            logger.info("Uploaded: %s/%s (%d bytes)", project, safe_name, len(file_data))
            self._send_json(201, {
                'status': 'created',
                'project': project,
                'build_number': build_number,
                'file': safe_name,
                'size': len(file_data),
                'path': str(dest_path.relative_to(config.root_dir))
            })

        except Exception as e:
            logger.exception("Upload error")
            self._send_error(500, f'Server error: {str(e)}')

    def _parse_boundary(self, content_type: str) -> Optional[bytes]:
        parts = content_type.split('boundary=')
        if len(parts) != 2:
            return None
        boundary = parts[1].strip().strip('"')
        return f'--{boundary}'.encode()

    def _parse_multipart(self, boundary: bytes, total_size: int) -> dict:
        data = self._read_exact(total_size)
        fields = {}
        parts = data.split(boundary)

        for part in parts:
            if not part.strip() or part.strip() == b'--':
                continue

            header_end = part.find(b'\r\n\r\n')
            if header_end == -1:
                continue

            headers_raw = part[:header_end].decode('utf-8', errors='ignore')
            body = part[header_end + 4:]

            if body.endswith(b'\r\n'):
                body = body[:-2]

            content_disposition = ''
            for line in headers_raw.split('\r\n'):
                if line.lower().startswith('content-disposition:'):
                    content_disposition = line
                    break

            name = ''
            filename = ''
            for item in content_disposition.split(';'):
                item = item.strip()
                if item.startswith('name='):
                    name = item[5:].strip('"')
                elif item.startswith('filename='):
                    filename = item[9:].strip('"')

            if name:
                if name not in fields:
                    fields[name] = []
                if filename:
                    fields[name].append(body)
                    fields[f'{name}_filename'] = [filename]
                else:
                    fields[name].append(body.decode('utf-8', errors='ignore'))

        return fields


def main() -> int:
    if not config.validate():
        return 1

    server = HTTPServer((config.host, config.port), ArtifactHandler)
    logger.info("Starting artifact server on %s:%d", config.host, config.port)
    logger.info("Root directory: %s", config.root_dir)
    logger.info("Max upload size: %d bytes", config.max_upload_size)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        server.server_close()

    return 0


if __name__ == '__main__':
    sys.exit(main())