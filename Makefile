# Specify Docker image and container names for the AI service
IMAGE_NAME ?= mariammohamed1112/ai-service
CONTAINER_NAME ?= ai-service-container
GROQ_API_KEY ?= api-key

# Build the Docker image using the Dockerfile
build:
	docker build -t $(IMAGE_NAME) .

# Run the Docker container with the API key
up:
	docker run -d --name $(CONTAINER_NAME) -p 5000:5000 -e GROQ_API_KEY=$(GROQ_API_KEY) $(IMAGE_NAME)

# Stop and remove the Docker container
down:
	@docker ps -aq --filter "name=$(CONTAINER_NAME)" | grep -q . && docker rm -f $(CONTAINER_NAME) || echo "No container to remove"

# Clean up unused Docker images and containers
clean:
	docker system prune -f

# Restart the container (stop, build, and run again)
restart:
	make down IMAGE_NAME=$(IMAGE_NAME) CONTAINER_NAME=$(CONTAINER_NAME)
	make build IMAGE_NAME=$(IMAGE_NAME)
	make up IMAGE_NAME=$(IMAGE_NAME) CONTAINER_NAME=$(CONTAINER_NAME) GROQ_API_KEY=$(GROQ_API_KEY)
