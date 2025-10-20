#!/bin/bash

# Production Deployment Script for Astro
# Usage: ./deploy.sh [start|stop|restart|logs|status]

set -e

COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.production"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env.production exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: $ENV_FILE not found!${NC}"
    echo "Please create $ENV_FILE with your production configuration."
    echo "See PRODUCTION_DEPLOYMENT.md for details."
    exit 1
fi

# Load environment variables
set -a
source "$ENV_FILE"
set +a

# Check required variables
REQUIRED_VARS=(
    "SECRET_KEY"
    "JWT_SECRET_KEY"
    "ENCRYPTION_KEY"
    "POSTGRES_PASSWORD"
    "OPENAI_API_KEY"
)

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}Error: Required environment variable $var is not set!${NC}"
        exit 1
    fi
done

# Function to display usage
usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start       - Start all services"
    echo "  stop        - Stop all services"
    echo "  restart     - Restart all services"
    echo "  logs        - View logs (follow mode)"
    echo "  status      - Check service status"
    echo "  build       - Rebuild and start services"
    echo "  backup      - Backup database"
    echo "  clean       - Stop services and clean up (WARNING: removes volumes)"
    echo ""
}

# Function to start services
start_services() {
    echo -e "${GREEN}Starting Astro services...${NC}"
    docker compose -f "$COMPOSE_FILE" up -d
    echo -e "${GREEN}Services started!${NC}"
    echo ""
    echo "Check status with: $0 status"
    echo "View logs with: $0 logs"
}

# Function to stop services
stop_services() {
    echo -e "${YELLOW}Stopping Astro services...${NC}"
    docker compose -f "$COMPOSE_FILE" down
    echo -e "${GREEN}Services stopped!${NC}"
}

# Function to restart services
restart_services() {
    echo -e "${YELLOW}Restarting Astro services...${NC}"
    docker compose -f "$COMPOSE_FILE" restart
    echo -e "${GREEN}Services restarted!${NC}"
}

# Function to view logs
view_logs() {
    echo -e "${GREEN}Viewing logs (Ctrl+C to exit)...${NC}"
    docker compose -f "$COMPOSE_FILE" logs -f
}

# Function to check status
check_status() {
    echo -e "${GREEN}Service Status:${NC}"
    docker compose -f "$COMPOSE_FILE" ps
    echo ""
    echo -e "${GREEN}Resource Usage:${NC}"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" \
        astro-frontend-prod astro-backend-prod astro-postgres-prod astro-redis-prod 2>/dev/null || true
}

# Function to build and start
build_services() {
    echo -e "${GREEN}Building and starting Astro services...${NC}"
    docker compose -f "$COMPOSE_FILE" up -d --build
    echo -e "${GREEN}Services built and started!${NC}"
}

# Function to backup database
backup_database() {
    BACKUP_DIR="backups"
    BACKUP_FILE="$BACKUP_DIR/astro_backup_$(date +%Y%m%d_%H%M%S).sql"
    
    mkdir -p "$BACKUP_DIR"
    
    echo -e "${GREEN}Creating database backup...${NC}"
    docker exec astro-postgres-prod pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > "$BACKUP_FILE"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Backup created successfully: $BACKUP_FILE${NC}"
        
        # Compress the backup
        gzip "$BACKUP_FILE"
        echo -e "${GREEN}Backup compressed: $BACKUP_FILE.gz${NC}"
    else
        echo -e "${RED}Backup failed!${NC}"
        exit 1
    fi
}

# Function to clean up
clean_services() {
    echo -e "${RED}WARNING: This will stop all services and remove volumes (data will be lost)!${NC}"
    read -p "Are you sure? (yes/no): " confirm
    
    if [ "$confirm" = "yes" ]; then
        echo -e "${YELLOW}Cleaning up...${NC}"
        docker compose -f "$COMPOSE_FILE" down -v
        echo -e "${GREEN}Cleanup complete!${NC}"
    else
        echo "Cancelled."
    fi
}

# Main script logic
case "${1:-}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    logs)
        view_logs
        ;;
    status)
        check_status
        ;;
    build)
        build_services
        ;;
    backup)
        backup_database
        ;;
    clean)
        clean_services
        ;;
    "")
        usage
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo ""
        usage
        exit 1
        ;;
esac

