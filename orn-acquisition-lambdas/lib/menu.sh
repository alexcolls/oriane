#!/bin/bash

# Source utils
LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$LIB_DIR/utils.sh"

# Function to list directories and let user select
select_directory() {
    local base_path="$1"
    local prompt="$2"
    local result_var="$3"
    
    check_directory "$base_path"
    
    # Get list of directories
    local dirs=($(find "$base_path" -maxdepth 1 -type d -not -path "$base_path" -exec basename {} \; | sort))
    
    if [ ${#dirs[@]} -eq 0 ]; then
        handle_error "No directories found in $base_path"
    fi
    
    printf "\n%s\n" "$prompt"
    printf "Available options:\n"
    
    for i in "${!dirs[@]}"; do
        printf "  %d. %s\n" $((i+1)) "${dirs[i]}"
    done
    
    while true; do
        printf "Select option (1-%d): " "${#dirs[@]}"
        read -r choice
        
        if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "${#dirs[@]}" ]; then
            if [ -n "$result_var" ]; then
                eval "$result_var='${dirs[$((choice-1))]}'"
            else
                echo "${dirs[$((choice-1))]}"
            fi
            return 0
        else
            printf "Invalid selection. Please choose a number between 1 and %d.\n" "${#dirs[@]}"
        fi
    done
}

# Function to confirm action
confirm_action() {
    local message="$1"
    echo -e "${YELLOW}$message${NC}"
    while true; do
        echo -n "Continue? (y/N): "
        read -r response
        case "$response" in
            [yY]|[yY][eE][sS])
                return 0
                ;;
            [nN]|[nN][oO]|"")
                echo "Operation cancelled."
                exit 0
                ;;
            *)
                echo -e "${RED}Please answer yes (y) or no (n).${NC}"
                ;;
        esac
    done
}

# Function to display selected configuration
display_selection() {
    local platform="$1"
    local lambda="$2"
    local image_name="$3"
    local lambda_path="$4"
    
    echo -e "${BLUE}Selected Configuration:${NC}"
    echo "  Platform: $platform"
    echo "  Lambda: $lambda"
    echo "  Image Name: $image_name"
    echo "  Lambda Path: $lambda_path"
    echo ""
}
