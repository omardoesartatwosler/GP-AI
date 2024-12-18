# Image name for your AI service
IMAGE_NAME=ai-service

# Build the Docker image
build:
	docker build -t $(IMAGE_NAME) .

# Run the Docker container
run:
	docker run -p 5000:5000 $(IMAGE_NAME)

# Stop and remove the running container
stop:
	docker stop $(shell docker ps -q --filter ancestor=$(IMAGE_NAME))

# Remove unused Docker resources
clean:
	docker system prune -f
