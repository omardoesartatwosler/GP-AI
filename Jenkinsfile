pipeline {
    agent any

    environment {
        IMAGE_NAME = "mariammohamed1112/ai-service" 
        MAKEFILE_PATH = "Makefile"
    }

    stages {
        stage('Checkout Code') {
            steps {
                echo 'Checking out source code...'
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                echo 'Building Docker image using Makefile...'
                sh 'make build'  
                sh 'docker images' // Verify the built image
            }
        }

        /* 
        stage('Run Tests') {
            steps {
                echo 'Running Tests...'
            }
        }
        */

        stage('Push Docker Image') {
            steps {
                echo 'Pushing Docker image to Docker Hub...'
                withCredentials([usernamePassword(credentialsId: 'docker-hub-credentials', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh 'echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin'
                }
                sh "docker tag ${IMAGE_NAME}:latest ${DOCKER_USER}/${IMAGE_NAME}:latest" // Tag the image
                sh "docker push ${DOCKER_USER}/${IMAGE_NAME}:latest" // Push to Docker Hub
            }
        }

        stage('Run Application') {
            steps {
                echo 'Running the application container...'
                sh 'make run' 
            }
        }
    }

    post {
        always {
            echo 'Pipeline execution completed. Printing container logs...'
            sh 'docker ps -a' 
        failure {
            echo 'Pipeline failed. Stopping containers...'
            sh 'make stop || true' 
        }
        success {
            echo 'Pipeline executed successfully!'
        }
    }
}
