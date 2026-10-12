pipeline {
    agent {
        docker {
            image 'gcc:14'
            args '-u root:root -v /var/run/docker.sock:/var/run/docker.sock'
        }
    }

    environment {
        ARTIFACT_SERVER_URL = credentials('artifact-server-url')
        ARTIFACT_SERVER_TOKEN = credentials('artifact-server-token')
        BUILD_NUMBER = "${BUILD_NUMBER}"
        BRANCH_NAME = "${BRANCH_NAME}"
    }

    options {
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Validate Configuration') {
            steps {
                sh '''
                    set -euo pipefail
                    echo "Validating ci-config.yaml..."
                    python3 -c "
import yaml, sys
try:
    with open('ci-config.yaml') as f:
        config = yaml.safe_load(f)
    required = ['project', 'build', 'tests', 'publish', 'output']
    for r in required:
        if r not in config:
            print(f'Missing required section: {r}')
            sys.exit(1)
    print('Configuration valid:', config['project']['name'])
"
                '''
            }
        }

        stage('Verify Tools') {
            steps {
                sh '''
                    set -euo pipefail
                    echo "=== Tool Versions ==="
                    gcc --version | head -1
                    cmake --version | head -1
                    ninja --version
                    git --version
                '''
            }
        }

        stage('Configure') {
            steps {
                dir('build') {
                    sh '''
                        set -euo pipefail
                        cmake -G Ninja \
                            -DCMAKE_BUILD_TYPE=Release \
                            -DBUILD_TESTS=ON \
                            ..
                    '''
                }
            }
        }

        stage('Build') {
            steps {
                dir('build') {
                    sh '''
                        set -euo pipefail
                        ninja
                    '''
                }
            }
        }

        stage('Test') {
            steps {
                dir('build') {
                    sh '''
                        set -euo pipefail
                        ctest --output-on-failure --parallel 4
                    '''
                }
            }
            post {
                always {
                    junit 'build/**/*.xml'
                }
            }
        }

        stage('Verify Artifacts') {
            steps {
                sh '''
                    set -euo pipefail
                    echo "=== Verifying Artifacts ==="
                    ls -la build/
                    if [[ ! -f "build/calculator_app" ]]; then
                        echo "ERROR: calculator_app not found"
                        exit 1
                    fi
                    ./build/calculator_app
                '''
            }
        }

        stage('Publish') {
            when {
                allOf {
                    branch 'main'
                    expression { return params.PUBLISH_ARTIFACTS != 'false' }
                }
            }
            steps {
                script {
                    if (env.ARTIFACT_SERVER_URL && env.ARTIFACT_SERVER_TOKEN) {
                        sh '''
                            set -euo pipefail
                            cd build
                            for artifact in calculator_app *.xml; do
                                if [[ -f "$artifact" ]]; then
                                    echo "Uploading $artifact..."
                                    response=$(curl -s -w "\n%{http_code}" \
                                        -X POST \
                                        -H "Authorization: Bearer ${ARTIFACT_SERVER_TOKEN}" \
                                        -F "project=CppBuildLab" \
                                        -F "build_number=${BUILD_NUMBER}" \
                                        -F "branch=${BRANCH_NAME}" \
                                        -F "file=@${artifact}" \
                                        "${ARTIFACT_SERVER_URL}/upload")
                                    http_code=$(echo "$response" | tail -n1)
                                    body=$(echo "$response" | head -n -1)
                                    if [[ "$http_code" -eq 200 ]] || [[ "$http_code" -eq 201 ]]; then
                                        echo "  Success: $body"
                                    else
                                        echo "  Failed (HTTP $http_code): $body"
                                        exit 1
                                    fi
                                fi
                            done
                        '''
                    } else {
                        echo "Artifact server credentials not configured. Skipping external publish."
                    }
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'build/calculator_app,build/*.xml', fingerprint: true, allowEmptyArchive: true
            cleanWs()
        }
        success {
            echo 'Build completed successfully!'
        }
        failure {
            echo 'Build failed!'
        }
        unstable {
            echo 'Build unstable (tests failed).'
        }
    }
}