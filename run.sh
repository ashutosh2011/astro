#!/bin/bash

# Astro MVP Backend - Docker Compose Management Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to start services
start_services() {
    print_status "Starting Astro MVP Backend services..."
    docker-compose up -d
    
    print_status "Waiting for services to be ready..."
    sleep 10
    
    # Check if services are healthy
    if docker-compose ps | grep -q "unhealthy"; then
        print_warning "Some services may not be fully ready yet. Check logs with: docker-compose logs"
    else
        print_success "All services are running!"
    fi
    
    print_status "Backend API available at: http://localhost:8000"
    print_status "API Documentation: http://localhost:8000/docs"
    print_status "Health Check: http://localhost:8000/healthz"
}

# Function to stop services
stop_services() {
    print_status "Stopping Astro MVP Backend services..."
    docker-compose down
    print_success "Services stopped."
}

# Function to restart services
restart_services() {
    print_status "Restarting Astro MVP Backend services..."
    docker-compose restart
    print_success "Services restarted."
}

# Function to view logs
view_logs() {
    if [ -n "$1" ]; then
        docker-compose logs -f "$1"
    else
        docker-compose logs -f backend
    fi
}

# Function to show status
show_status() {
    print_status "Service Status:"
    docker-compose ps
}

# Function to clean up (remove volumes)
cleanup() {
    print_warning "This will remove all data (databases, cache, etc.). Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        print_status "Removing all data and stopping services..."
        docker-compose down -v
        print_success "Cleanup completed."
    else
        print_status "Cleanup cancelled."
    fi
}

# Function to show help
show_help() {
    echo "Astro MVP Backend - Docker Compose Management"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     Start all services (default)"
    echo "  stop      Stop all services"
    echo "  restart   Restart all services"
    echo "  logs      View backend logs (use 'logs [service]' for specific service)"
    echo "  status    Show service status"
    echo "  cleanup   Remove all data and stop services"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 logs postgres"
    echo "  $0 status"
}

# Main script logic
main() {
    check_docker
    
    case "${1:-start}" in
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
            view_logs "$2"
            ;;
        status)
            show_status
            ;;
        cleanup)
            cleanup
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
