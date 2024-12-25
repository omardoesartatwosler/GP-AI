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
                sh "make build IMAGE_NAME=${IMAGE_NAME}"
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
                sh "docker tag ${IMAGE_NAME}:latest ${IMAGE_NAME}:latest" // Tag the image
                sh "docker push ${IMAGE_NAME}:latest" // Push to Docker Hub
            }
        }

        stage('Run Application') {
            steps {
                echo 'Running the application container...'
                sh "make down CONTAINER_NAME=ai-service-container"
                sh "make up IMAGE_NAME=${IMAGE_NAME} GROQ_API_KEY=${GROQ_API_KEY} CONTAINER_NAME=ai-service-container"
            }
        }
    }

    post {
        always {
            echo 'Pipeline execution completed. Printing container logs...'
            sh 'docker ps -a' 
        failure {
            echo 'Pipeline failed. Stopping containers...'
            sh  "make down IMAGE_NAME=${IMAGE_NAME}"
        }
        success {
            echo 'Pipeline executed successfully!'
        }
    }
}
