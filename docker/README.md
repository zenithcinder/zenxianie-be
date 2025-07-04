# Docker Deployment Guide

This directory contains the Docker Compose configuration for deploying the zenxianie [REDACTED] application in a production environment.

## Prerequisites

- Docker Engine 20.10.0 or later
- Docker Compose 2.0.0 or later
- Docker Swarm mode enabled
- GitHub Container Registry (ghcr.io) access
- A domain name for your application

## GitHub Container Registry Setup

### 1. Create GitHub Personal Access Token (PAT)
1. Go to GitHub Settings > Developer settings > Personal access tokens > Tokens (classic)
2. Click "Generate new token"
3. Give it a name (e.g., "Docker Registry Access")
4. Select these scopes:
   - `write:packages`
   - `read:packages`
   - `delete:packages`
5. Copy the generated token (you'll need it later)

### 2. Login to GitHub Container Registry
```bash
# Replace YOUR_GITHUB_USERNAME with your actual GitHub username
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

### 3. Building and Pushing Images

#### Build the image:
```bash
# From your project root directory
docker build -t ghcr.io/YOUR_GITHUB_USERNAME/zenxianie-[REDACTED]-app:latest .
```

#### Push the image:
```bash
docker push ghcr.io/YOUR_GITHUB_USERNAME/zenxianie-[REDACTED]-app:latest
```

#### Tag specific versions:
```bash
# Build with a specific tag
docker build -t ghcr.io/YOUR_GITHUB_USERNAME/zenxianie-[REDACTED]-app:v1.0.0 .

# Push the tagged version
docker push ghcr.io/YOUR_GITHUB_USERNAME/zenxianie-[REDACTED]-app:v1.0.0
```

### 4. Managing Package Visibility
1. Go to your GitHub repository
2. Click on "Packages"
3. Find your package
4. Click on "Package settings"
5. Under "Danger Zone", click "Change visibility"
6. Choose "Public" if you want others to be able to pull the image

### 5. Pulling Images
```bash
# Login first (if not already logged in)
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin

# Pull the image
docker pull ghcr.io/YOUR_GITHUB_USERNAME/zenxianie-[REDACTED]-app:latest
```

### 6. Testing Images Locally
```bash
# Run the container
docker run -p 8011:8011 ghcr.io/YOUR_GITHUB_USERNAME/zenxianie-[REDACTED]-app:latest
```

### 7. Managing Images
```bash
# List your images
docker images | grep ghcr.io

# Remove a local image
docker rmi ghcr.io/YOUR_GITHUB_USERNAME/zenxianie-[REDACTED]-app:latest
```

### 8. Best Practices
1. Always use specific version tags for production deployments
2. Keep your GitHub token secure and never commit it to version control
3. Regularly update your base images for security patches
4. Use multi-stage builds to keep image sizes small
5. Implement proper health checks in your Dockerfile
6. Use .dockerignore to exclude unnecessary files

## Environment Setup

### 1. Create .env File
Create a `.env` file in the same directory as `app.deploy.yml` with the following variables:

```env
# Docker Registry
DOCKER_REGISTRY=ghcr.io/your-username
APP_VERSION=latest
POSTGRES_VERSION=14
REDIS_VERSION=7-alpine

# Domain
DOMAIN_NAME=yourdomain.com

# Database
POSTGRES_DB=zenxianie_[REDACTED]
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Django
DJANGO_SECRET_KEY=your_secret_key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DJANGO_CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# App Resources
APP_REPLICAS=3
APP_CPU_LIMIT=0.50
APP_MEMORY_LIMIT=512M
APP_CPU_RESERVATION=0.25
APP_MEMORY_RESERVATION=256M

# Database Resources
DB_CPU_LIMIT=1.0
DB_MEMORY_LIMIT=1G
DB_CPU_RESERVATION=0.5
DB_MEMORY_RESERVATION=512M

# Redis Resources
REDIS_CPU_LIMIT=0.5
REDIS_MEMORY_LIMIT=512M
REDIS_CPU_RESERVATION=0.25
REDIS_MEMORY_RESERVATION=256M
```

### 2. Environment Variables Explanation

#### Django Settings
- `DJANGO_SECRET_KEY`: Used for cryptographic signing. Generate a secure key for production.
- `DJANGO_DEBUG`: Set to `False` in production. Controls debug mode and security settings.
- `DJANGO_ALLOWED_HOSTS`: Comma-separated list of allowed host names.
- `DJANGO_CORS_ALLOWED_ORIGINS`: Comma-separated list of allowed CORS origins.

#### Database Settings
- `POSTGRES_DB`: Database name
- `POSTGRES_USER`: Database user
- `POSTGRES_PASSWORD`: Database password
- `POSTGRES_HOST`: Database host (use 'db' in Docker)
- `POSTGRES_PORT`: Database port

#### Redis Settings
- `REDIS_HOST`: Redis host (use 'redis' in Docker)
- `REDIS_PORT`: Redis port

#### Resource Limits
- `APP_REPLICAS`: Number of application containers
- `APP_CPU_LIMIT`: CPU limit per app container
- `APP_MEMORY_LIMIT`: Memory limit per app container
- `DB_CPU_LIMIT`: CPU limit for database
- `DB_MEMORY_LIMIT`: Memory limit for database
- `REDIS_CPU_LIMIT`: CPU limit for Redis
- `REDIS_MEMORY_LIMIT`: Memory limit for Redis

### 3. Create traefik.yml
Create a `traefik.yml` file for Traefik configuration:

```yaml
api:
  dashboard: true
  insecure: true

entryPoints:
  web:
    address: ":80"
  websecure:
    address: ":443"
  ws:
    address: ":8001"
    http:
      upgrade: true
      upgrade.websocket: true

providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    swarmMode: true
    exposedByDefault: false
```

## Deployment Steps

1. Initialize Docker Swarm (if not already initialized):
```bash
docker swarm init
```

2. Login to GitHub Container Registry:
```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
```

3. Deploy the stack:
```bash
docker stack deploy -c app.deploy.yml zenxianie-[REDACTED]
```

4. Check the deployment status:
```bash
docker stack services zenxianie-[REDACTED]
```

## Service Access

- Web Application: `http://yourdomain.com`
- WebSocket: `ws://yourdomain.com:8001`
- Traefik Dashboard: `http://yourdomain.com:8080`

## Scaling

To scale the application:
```bash
docker service scale zenxianie-[REDACTED]_app=5
```

## Monitoring

View logs for a specific service:
```bash
docker service logs zenxianie-[REDACTED]_app
```

## Backup

The following volumes are created:
- `postgres_data`: PostgreSQL database files
- `redis_data`: Redis data
- `traefik_data`: Traefik configuration
- `traefik_logs`: Traefik logs

To backup the database:
```bash
docker exec -t postgres-db pg_dump -U postgres zenxianie_[REDACTED] > backup.sql
```

## Troubleshooting

1. Check service status:
```bash
docker service ls
```

2. View detailed service information:
```bash
docker service inspect zenxianie-[REDACTED]_app
```

3. Check container logs:
```bash
docker service logs zenxianie-[REDACTED]_app
```

4. Restart a service:
```bash
docker service update --force zenxianie-[REDACTED]_app
```

## Security Considerations

1. Keep your `.env` file secure and never commit it to version control
2. Use strong passwords for database and Redis
3. Keep your Docker images updated
4. Regularly backup your data
5. Monitor system resources and logs
6. Use specific version tags for production deployments
7. Implement proper health checks
8. Use secrets management for sensitive data
9. Set `DJANGO_DEBUG=False` in production
10. Configure proper CORS settings for your domain
11. Use HTTPS in production
12. Regularly rotate secrets and passwords

## Cleanup

To remove the stack:
```bash
docker stack rm zenxianie-[REDACTED]
```

To leave the swarm:
```bash
docker swarm leave --force
``` 