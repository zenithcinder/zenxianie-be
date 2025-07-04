# Zenxianie [REDACTED] Backend

The backend service for Zenxianie [REDACTED], a smart parking management system providing real-time parking space availability, reservations, and automated payment processing.

## Features

- Real-time parking space monitoring
- WebSocket-based notifications
- JWT Authentication
- RESTful API
- Admin dashboard
- Database management
- Payment processing
- Report generation
- Advanced notification system with real-time updates
- Comprehensive reporting with data validation
- Role-based access control
- Automated deployment with GitHub Actions

## Tech Stack

- Django 5.0.2
- Django REST Framework 3.14.0
- Channels 4.0.0 (WebSocket)
- PostgreSQL 14+
- Redis 7+
- JWT Authentication
- Docker & Docker Swarm
- Traefik (Reverse Proxy)
- GitHub Container Registry (ghcr.io)

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 14+
- Redis 7+

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/[REDACTED]/zenxianie-BE.git
cd zenxianie-[REDACTED]-BE
```

2. Set up the development environment:
```bash
# Install pipenv if you don't have it
pip install pipenv

# Install dependencies using Pipenv
pipenv install

# Activate the virtual environment
pipenv shell

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run migrations
pipenv run python manage.py migrate

# Create superuser
pipenv run python manage.py createsuperuser

# Run development server
pipenv run python manage.py runserver
```

## Docker Development

1. Local Development (with local database):
```bash
docker-compose -f docker/app.local.db.yml up --build
```

2. Local Development (with containerized database):
```bash
docker-compose -f docker/app.local.yml up --build
```

3. Access the services:
- API: http://localhost:8011
- Admin Interface: http://localhost:8011/admin
- API Documentation: http://localhost:8011/api/docs/

## Testing

Run the test suite using Docker:
```bash
# Run all tests
./scripts/run_tests.sh

# Or manually using Docker Compose
docker-compose -f docker/app.test.yml up --build
```

## Project Structure

```
back-end/
├── app/
│   ├── api/               # API endpoints
│   │   ├── accounts/     # User management
│   │   ├── parking_lots/ # Parking lot management
│   │   ├── reservations/ # Reservation system
│   │   ├── reports/      # Report generation
│   │   ├── jwt_blacklist/# JWT token management
│   │   ├── notification/ # Notification system
│   │   └── realtime/     # WebSocket handling
│   ├── config/           # Django settings
│   ├── test/            # Test modules
│   │   ├── accounts/    # Account tests
│   │   ├── parking_lots/# Parking lot tests
│   │   ├── reservations/# Reservation tests
│   │   └── reports/     # Report tests
│   └── utils/           # Utility functions
├── docker/              # Docker configuration
│   ├── app.local.yml   # Local development compose file
│   ├── app.local.db.yml# Local development with local DB
│   ├── app.test.yml    # Test environment compose file
│   ├── app.deploy.yml  # Production compose file
│   └── traefik.yml     # Traefik configuration
├── scripts/            # Utility scripts
│   └── run_tests.sh   # Test runner script
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Environment Variables

The application uses environment variables for configuration. You can set these up in two ways:

1. Using a `.env` file (recommended for local development):
   ```bash
   # Copy the example file
   cp .env.example .env
   
   # Edit the .env file with your settings
   nano .env
   ```

2. Setting environment variables directly (recommended for production):
   ```bash
   export DJANGO_SECRET_KEY=your-secret-key
   export DJANGO_DEBUG=False
   # ... etc
   ```

### Required Environment Variables

```env
# Django Settings
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_CORS_ALLOWED_ORIGINS=http://localhost:5173

# Database Settings
POSTGRES_DB=zenxianie_[REDACTED]
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Redis Settings
REDIS_HOST=localhost
REDIS_PORT=6379

# Channel Layers Settings
CHANNEL_LAYERS_REDIS_HOST=localhost
CHANNEL_LAYERS_REDIS_PORT=6379
```

### Environment Variables in Different Environments

- **Local Development**: Use `.env` file
- **Testing**: Environment variables are set in GitHub Actions workflow
- **Staging/Production**: Environment variables are set in Docker Compose files

## API Documentation

The API is fully documented using Swagger UI. To view the complete API documentation with all available endpoints, methods, request/response formats, and to test the API directly:

- **Swagger UI**: http://localhost:8000/swagger/
- **ReDoc**: http://localhost:8000/redoc/

These interactive documentation pages provide a complete reference for all API endpoints, making it easy to understand and test the available functionality.

## WebSocket Events

The system uses WebSocket for real-time updates. Available events:

- `parking_space_update`: Updates when parking space status changes
- `reservation_update`: Updates when reservation status changes
- `payment_update`: Updates when payment status changes
- `notification`: Real-time notifications for:
  - New reservations
  - Expired reservations
  - Cancelled reservations
  - Upcoming reservations (30 minutes before start)

## API Modules Overview

The API is organized into several main functional modules:

### Authentication and User Management
- User registration and authentication
- JWT token handling (access and refresh tokens)
- Profile management
- User administration for staff members

### Parking Management
- Parking lot and space management
- Real-time availability tracking
- Geolocation-based searching
- Occupancy rate monitoring

### Reservation System
- Create, update and cancel reservations
- Automated status management (active, completed, cancelled)
- Vehicle tracking
- Duration and cost calculations

### Notifications
- User notification management
- Real-time updates via WebSockets
- Notification preferences and settings
- Read/unread status tracking

### Reports and Analytics
- Daily, monthly and custom timeframe reports
- Revenue analysis
- Occupancy tracking
- Peak time analysis
- Data export functionality

For complete documentation of all endpoints, request/response formats, and authentication requirements, please refer to the Swagger documentation at `/swagger/` when the server is running.

## Security

- JWT Authentication for all API endpoints
- WebSocket authentication with short-lived tokens
- CORS configuration
- SQL injection protection
- XSS protection
- CSRF protection
- Rate limiting
- Input validation
- Password hashing and validation
- Role-based access control
- Secure WebSocket connections
- Data validation for reports and statistics

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Production Deployment

For production deployment instructions, see the [Docker Deployment Guide](docker/README.md).

### GitHub Container Registry Setup

1. Create a GitHub Personal Access Token (PAT) with `write:packages` scope
2. Login to GitHub Container Registry:
```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

3. Build and push the image:
```bash
docker build -t ghcr.io/YOUR_GITHUB_USERNAME/zenxianie-[REDACTED]-app:latest .
docker push ghcr.io/YOUR_GITHUB_USERNAME/zenxianie-[REDACTED]-app:latest
```

4. Deploy using Docker Swarm:
```bash
docker stack deploy -c docker/app.deploy.yml zenxianie
```

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration and deployment:

- Automated testing on pull requests
- Docker image building and pushing
- Automated deployment to staging/production
- Security scanning
- Code quality checks

For more details, see the workflow files in `.github/workflows/`.
