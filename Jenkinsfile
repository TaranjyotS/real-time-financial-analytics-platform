pipeline {
  agent any
  stages {
    stage('Backend Tests') { steps { sh 'pip install -r backend/requirements.txt && pytest backend/tests' } }
    stage('Frontend Build') { steps { sh 'cd frontend && npm install && npm run build' } }
    stage('Docker Build') { steps { sh 'docker compose -f infrastructure/docker-compose.yml build' } }
  }
}
