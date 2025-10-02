#!/bin/bash

# Configuration
ACCOUNT_ID="509399609859"
AWS_REGION="us-east-1"
ROLE="OrianeCollector"

# Colors for output (only if terminal supports it)
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m' # No Color
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    NC=''
fi

# Cleanup function
cleanup() {
    # Clean up any remaining tar files in current directory
    local tar_files=(*.tar)
    if [ -e "${tar_files[0]}" ]; then
        echo -e "${YELLOW}Cleaning up remaining temporary tar files...${NC}"
        rm -f *.tar
        echo -e "${GREEN}Cleanup complete${NC}"
    fi
    
    # Legacy cleanup for IMAGE_NAME variable (kept for compatibility)
    if [ -n "$IMAGE_NAME" ] && [ -f "${IMAGE_NAME}.tar" ]; then
        echo -e "${YELLOW}Cleaning up temporary files...${NC}"
        rm -f "${IMAGE_NAME}.tar"
        echo -e "${GREEN}Legacy cleanup complete${NC}"
    fi
}

# Error handling function
handle_error() {
    local message="$1"
    echo -e "${RED}Error: $message${NC}" >&2
    cleanup
    exit 1
}

# Success message function
success_message() {
    local message="$1"
    echo -e "${GREEN}$message${NC}"
}

# Info message function
info_message() {
    local message="$1"
    echo -e "${YELLOW}$message${NC}"
}

# Check if directory exists
check_directory() {
    local dir="$1"
    if [ ! -d "$dir" ]; then
        handle_error "Directory '$dir' does not exist"
    fi
}

# Check if file exists
check_file() {
    local file="$1"
    if [ ! -f "$file" ]; then
        return 1
    fi
    return 0
}

# Extract IMAGE_NAME from .env file
get_image_name() {
    local lambda_path="$1"
    local env_file="$lambda_path/.env"
    
    if ! check_file "$env_file"; then
        echo -e "${RED}Error: No .env file found in $lambda_path${NC}" >&2
        echo -e "${YELLOW}Please create a .env file with the following format:${NC}" >&2
        echo -e "${YELLOW}IMAGE_NAME=your-image-name-here${NC}" >&2
        echo "" >&2
        echo -e "${YELLOW}Example for this lambda:${NC}" >&2
        local lambda_name=$(basename "$lambda_path")
        local platform_name=$(basename "$(dirname "$lambda_path")")
        echo -e "${YELLOW}IMAGE_NAME=${platform_name}-${lambda_name}-collector${NC}" >&2
        exit 1
    fi
    
    local image_name=$(grep "^IMAGE_NAME=" "$env_file" | cut -d'=' -f2 | tr -d '"' | tr -d "'")
    
    if [ -z "$image_name" ]; then
        echo -e "${RED}Error: IMAGE_NAME not found in $env_file${NC}" >&2
        echo -e "${YELLOW}Please add IMAGE_NAME to your .env file:${NC}" >&2
        echo -e "${YELLOW}IMAGE_NAME=your-image-name-here${NC}" >&2
        exit 1
    fi
    
    echo "$image_name"
}

# Derive FUNCTION_NAME from .env or path
get_function_name() {
    local lambda_path="$1"
    local env_file="$lambda_path/.env"

    if check_file "$env_file"; then
        local fn=$(grep "^FUNCTION_NAME=" "$env_file" | cut -d'=' -f2 | tr -d '"' | tr -d "'")
        if [ -n "$fn" ]; then
            echo "$fn"
            return 0
        fi
    fi
    # Fallback: derive name as orn-<platform>-<lambda>
    local lambda_name=$(basename "$lambda_path")
    local platform_name=$(basename "$(dirname "$lambda_path")")
    echo "orn-${platform_name}-${lambda_name}"
}

# Get ALIAS_NAME from .env or default to "live"
get_alias_name() {
    local lambda_path="$1"
    local env_file="$lambda_path/.env"
    local alias="live"
    if check_file "$env_file"; then
        local from_env=$(grep "^ALIAS_NAME=" "$env_file" | cut -d'=' -f2 | tr -d '"' | tr -d "'")
        if [ -n "$from_env" ]; then
            alias="$from_env"
        fi
    fi
    echo "$alias"
}

# Canary rollout settings
get_canary_weight() {
    local lambda_path="$1"
    local env_file="$lambda_path/.env"
    local weight="0.1" # 10%
    if check_file "$env_file"; then
        local from_env=$(grep "^CANARY_WEIGHT=" "$env_file" | cut -d'=' -f2 | tr -d '"' | tr -d "'")
        if [ -n "$from_env" ]; then
            weight="$from_env"
        fi
    fi
    echo "$weight"
}

get_canary_wait_seconds() {
    local lambda_path="$1"
    local env_file="$lambda_path/.env"
    local wait="300" # 5 minutes
    if check_file "$env_file"; then
        local from_env=$(grep "^CANARY_WAIT_SECONDS=" "$env_file" | cut -d'=' -f2 | tr -d '"' | tr -d "'")
        if [ -n "$from_env" ]; then
            wait="$from_env"
        fi
    fi
    echo "$wait"
}

# Check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        handle_error "Docker is not running or not accessible"
    fi
}

# Check if AWS CLI is available and configured
check_aws() {
    if ! command -v aws >/dev/null 2>&1; then
        handle_error "AWS CLI is not installed"
    fi
    
    if ! aws sts get-caller-identity >/dev/null 2>&1; then
        handle_error "AWS CLI is not configured or credentials are invalid"
    fi
}

# Validate lambda directory structure
validate_lambda_structure() {
    local lambda_path="$1"
    
    if ! check_file "$lambda_path/Dockerfile"; then
        handle_error "No Dockerfile found in $lambda_path"
    fi
}
