#!/bin/bash

# =============================================================================
# Master Script for Search API Operations
# =============================================================================
# This script provides a menu-driven interface for all search API operations
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== Search API Operations Menu ==="
echo "Project root: $PROJECT_ROOT"
echo ""

# Function to display menu
show_menu() {
    echo "Available operations:"
    echo "  1. Setup KinD cluster"
    echo "  2. Build and deploy to KinD"
    echo "  3. Test search API on KinD"
    echo "  4. Deploy to EKS"
    echo "  5. Cleanup KinD cluster"
    echo "  6. Run all (setup + build + test)"
    echo "  7. Exit"
    echo ""
}

# Function to execute script with error handling
execute_script() {
    local script_path="$1"
    local description="$2"
    
    echo "=== $description ==="
    echo "Executing: $script_path"
    
    if [ -f "$script_path" ]; then
        if bash "$script_path"; then
            echo "✓ $description completed successfully"
        else
            echo "✗ $description failed"
            exit 1
        fi
    else
        echo "ERROR: Script not found: $script_path"
        exit 1
    fi
    
    echo ""
}

# Function to make scripts executable
make_executable() {
    chmod +x "$SCRIPT_DIR"/*.sh
}

# Main menu loop
main() {
    cd "$PROJECT_ROOT"
    make_executable
    
    while true; do
        show_menu
        read -p "Select an option (1-7): " choice
        
        case $choice in
            1)
                execute_script "$SCRIPT_DIR/setup-kind-cluster.sh" "KinD Cluster Setup"
                ;;
            2)
                execute_script "$SCRIPT_DIR/build-and-deploy.sh" "Build and Deploy to KinD"
                ;;
            3)
                execute_script "$SCRIPT_DIR/test-search-api.sh" "Test Search API"
                ;;
            4)
                execute_script "$SCRIPT_DIR/deploy-to-eks.sh" "Deploy to EKS"
                ;;
            5)
                execute_script "$SCRIPT_DIR/cleanup-kind-cluster.sh" "Cleanup KinD Cluster"
                ;;
            6)
                echo "=== Running Full Pipeline ==="
                execute_script "$SCRIPT_DIR/setup-kind-cluster.sh" "KinD Cluster Setup"
                execute_script "$SCRIPT_DIR/build-and-deploy.sh" "Build and Deploy to KinD"
                execute_script "$SCRIPT_DIR/test-search-api.sh" "Test Search API"
                echo "✓ Full pipeline completed successfully"
                ;;
            7)
                echo "Exiting..."
                exit 0
                ;;
            *)
                echo "Invalid option. Please select 1-7."
                ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
        echo ""
    done
}

# Run main function
main
