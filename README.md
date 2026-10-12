# CppBuildLab

CI/CD laboratory with Jenkins, Docker, and C++20.

## Overview

This project demonstrates a complete CI/CD pipeline for a C++ application:
- **C++20** application with Calculator class
- **CMake + Ninja** build system
- **GoogleTest** for unit testing (via FetchContent)
- **Docker** for reproducible build environments
- **Jenkins** pipeline (declarative)
- **Python** artifact server for build artifact storage

## Prerequisites

### Local Development
- GCC 11+ or Clang 13+
- CMake 3.20+
- Ninja
- Git
- Python 3.8+ (for artifact server)

### Jenkins in Docker
- Docker Engine 20+
- Docker Compose (optional)
- At least 4GB RAM for Jenkins container

### Windows Artifact Server
- Python 3.8+
- Write access to `D:\Builds` (or configured directory)

## Quick Start (Local Build)

```bash
# Clone
git clone <repo-url>
cd CppBuildLab

# Configure and build
cmake -G Ninja -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTS=ON
ninja -C build

# Run tests
cd build && ctest --output-on-failure

# Run application
./build/calculator_app
```

## Running the Artifact Server

### Windows (PowerShell)

```powershell
cd artifact-server
$env:ARTIFACT_ROOT_DIR = "D:\Builds"
$env:ARTIFACT_SERVER_TOKEN = "your-secure-random-token"
$env:ARTIFACT_SERVER_PORT = "8080"
python server.py
```

### Linux/macOS

```bash
cd artifact-server
export ARTIFACT_ROOT_DIR="/var/builds"
export ARTIFACT_SERVER_TOKEN="your-secure-random-token"
export ARTIFACT_SERVER_PORT=8080
python3 server.py
```

Verify it's running:
```bash
curl http://localhost:8080/health
# {"status": "ok"}
```

## Jenkins Setup

### 1. Run Jenkins in Docker

```bash
# Create network for Jenkins to reach artifact server
docker network create jenkins-net

# Run Jenkins (with Docker socket for agent containers)
docker run -d \
  --name jenkins \
  --network jenkins-net \
  -p 8080:8080 -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  jenkins/jenkins:lts
```

> **Note:** Mounting Docker socket gives Jenkins full host access. For production, use a dedicated Docker agent.

### 2. Initial Jenkins Setup

1. Open `http://localhost:8080`
2. Get initial password: `docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword`
3. Install suggested plugins
4. Create admin user

### 3. Configure Credentials

In Jenkins → Credentials → System → Global credentials → Add Credentials:

| Kind | Scope | ID | Description |
|------|-------|----|-------------|
| Secret text | Global | `artifact-server-url` | `http://host.docker.internal:8080` |
| Secret text | Global | `artifact-server-token` | Your token from server config |

> **Windows Docker Desktop:** Use `host.docker.internal` to reach host from container.
> **Linux:** Use host IP or `172.17.0.1` (docker0 gateway).

### 4. Create Pipeline Job

1. New Item → Pipeline → Name: `CppBuildLab`
2. Pipeline → Definition: Pipeline script from SCM
3. SCM: Git → Repository URL: your repo
4. Branch: `*/main`
5. Script Path: `Jenkinsfile`
6. Save

### 5. Run Build

Click "Build Now". Check Console Output for progress.

## Project Structure

```
CppBuildLab/
├── Jenkinsfile           # Jenkins declarative pipeline
├── ci-config.yaml        # CI configuration
├── CMakeLists.txt        # CMake build configuration
├── Dockerfile.build      # Custom build image (optional)
├── src/
│   ├── main.cpp          # Application entry point
│   ├── calculator.hpp    # Calculator class declaration
│   └── calculator.cpp    # Calculator implementation
├── tests/
│   └── calculator_tests.cpp  # GoogleTest unit tests
├── ci/
│   ├── build.sh          # Build script
│   ├── test.sh           # Test script
│   └── publish.sh        # Artifact publish script
└── artifact-server/
    ├── server.py         # Python artifact server
    ├── requirements.txt  # No deps (stdlib only)
    └── README.md
```

## Configuration

### ci-config.yaml

Controls pipeline behavior:

```yaml
project:
  name: "CppBuildLab"
  language: "cpp"
  standard: 20

build:
  image: "gcc:14"
  generator: "Ninja"
  cmake_options:
    - "-DCMAKE_BUILD_TYPE=Release"
    - "-DBUILD_TESTS=ON"

tests:
  enabled: true
  command: "ctest --output-on-failure --parallel 4"

publish:
  enabled: true
  branch: "main"
  require_tests: true
  server:
    url_env: "ARTIFACT_SERVER_URL"
    token_env: "ARTIFACT_SERVER_TOKEN"
```

## Testing Failure Scenarios

### 1. Force Test Failure

Edit `tests/calculator_tests.cpp`:
```cpp
TEST_F(CalculatorTest, ForceFail) {
    EXPECT_EQ(1, 2);  // This will fail
}
```

Push to main → Jenkins build fails → No artifacts published.

### 2. Force Build Failure

Edit `src/calculator.cpp`:
```cpp
double Calculator::add(double a, double b) const {
    return a + b + ;  // Syntax error
}
```

Push → Build fails early.

### 3. Disable Publishing

In Jenkins, rebuild with parameter `PUBLISH_ARTIFACTS=false`.

## Accessing Published Artifacts

On Windows server machine:
```
D:\Builds\CppBuildLab\<BUILD_NUMBER>\
  calculator_app
  test_results.xml
```

Or via HTTP (if server exposes download endpoint - not implemented in basic version).

## Troubleshooting

### Jenkins can't reach artifact server

- **Windows Docker Desktop**: Use `http://host.docker.internal:8080`
- **Linux**: Use `http://<host-ip>:8080` or `http://172.17.0.1:8080`
- Check firewall allows port 8080
- Verify server is running: `curl http://<server>:8080/health`

### Docker permission denied

```bash
# Add jenkins user to docker group (inside container)
docker exec -u root jenkins usermod -aG docker jenkins
docker restart jenkins
```

### CMake/Ninja not found in container

The pipeline uses `gcc:14` image which includes GCC but not CMake/Ninja by default.
The Jenkinsfile assumes they are installed. Options:
1. Use custom `Dockerfile.build` image
2. Install in pipeline: `apt-get update && apt-get install -y cmake ninja-build`
3. Use `docker run --entrypoint` with a prepared image

### Tests not found

Ensure `BUILD_TESTS=ON` in CMake options and `enable_testing()` in CMakeLists.txt.

### Artifacts not uploaded

- Check `ARTIFACT_SERVER_URL` and `ARTIFACT_SERVER_TOKEN` credentials exist
- Verify `publish` stage runs (only on `main` branch by default)
- Check Jenkins console for curl errors

## Security Considerations

- **Artifact server**: No HTTPS, no rate limiting, token auth only. Lab use only.
- **Docker socket**: Mounting `/var/run/docker.sock` gives root-equivalent access. Use dedicated agents for production.
- **Credentials**: Never commit tokens to repo. Use Jenkins Credentials store.

## Extending

### Add SDL3 Support

1. Enable in CMake: `-DUSE_SDL3=ON`
2. Install SDL3 development packages in build image
3. Add SDL3 code in `src/`

### Add More Tests

Add test files in `tests/` and they'll be picked up automatically by CTest.

### Add Static Analysis

Add `cppcheck` or `clang-tidy` to build stage.

## License

MIT License - Feel free to use for learning and experiments.