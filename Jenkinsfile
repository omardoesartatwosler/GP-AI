pipeline {
    agent any

    environment {
        IMAGE_NAME      = "mariammohamed1112/ai-service"
        IMAGE_TAG       = "latest"
        REMOTE_HOST     = "ubuntu@54.161.76.143"        
        REMOTE_DIR      = "/home/ubuntu/GP-AI"         
        CONTAINER_NAME  = "ai-service-container"
        GROQ_API_KEY    = "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"
    }

    stages {
        stage('Checkout Code') {
            steps {
                echo ' Checking out source code...'
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                echo ' Building Docker image using Makefile...'
                sh "make build IMAGE_NAME=${IMAGE_NAME}"
                sh 'docker images'
            }
        }

        stage('Push Docker Image') {
            steps {
                echo ' Pushing Docker image to Docker Hub...'
                withCredentials([usernamePassword(
                    credentialsId: 'docker-hub-credentials',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                        docker tag ${IMAGE_NAME}:latest ${IMAGE_NAME}:${IMAGE_TAG}
                        docker push ${IMAGE_NAME}:${IMAGE_TAG}
                    '''
                }
            }
        }

        stage('Deploy on EC2') {
            steps {
                echo ' Deploying AI service to EC2 instance...'
                sshagent(['ec2-key-jenkins']) {
                    sh """
                        ssh -tt -o StrictHostKeyChecking=no ${REMOTE_HOST} << EOF
                            set -e
                            echo " Stopping and removing old container..."
                            docker stop ${CONTAINER_NAME} || true
                            docker rm ${CONTAINER_NAME} || true

                            echo " Pulling latest image..."
                            docker pull ${IMAGE_NAME}:${IMAGE_TAG}

                            echo " Running new container..."
                            docker run -d --name ${CONTAINER_NAME} \\
                                --restart always \\
                                -e GROQ_API_KEY="${GROQ_API_KEY}" \\
                                -p 8000:8000 \\
                                ${IMAGE_NAME}:${IMAGE_TAG}

                            echo " Deployment complete. Active containers:"
                            docker ps -a
                        EOF
                    """
                }
            }
        }
    }

    post {
        always {
            echo ' Pipeline execution completed.'
        }
        failure {
            echo ' Pipeline failed. Deployment to EC2 was not successful.'
        }
        success {
            echo ' Pipeline executed and deployed AI service successfully to EC2.'
        }
    }
}
