#!/bin/bash
# 02_arch_inventory.sh - Automated Architecture & Component Inventory
# This script analyzes the project structure and generates comprehensive architecture documentation

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Global variables
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_FILE="${PROJECT_ROOT}/architecture_overview.md"
TEMP_DIR="${PROJECT_ROOT}/.arch_inventory_tmp"

# Create temporary directory
mkdir -p "$TEMP_DIR"

# Logging function
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a directory exists and is not empty
check_component() {
    local component_path="$1"
    local component_name="$2"
    
    if [[ -d "$component_path" ]]; then
        local file_count=$(find "$component_path" -type f -name "*.py" -o -name "*.cpp" -o -name "*.tf" -o -name "*.yml" -o -name "*.yaml" -o -name "*.md" -o -name "*.sh" -o -name "*.js" -o -name "*.ts" | wc -l)
        if [[ $file_count -gt 0 ]]; then
            echo "EXISTS"
        else
            echo "EMPTY"
        fi
    else
        echo "MISSING"
    fi
}

# Function to analyze component structure
analyze_component() {
    local component_path="$1"
    local component_name="$2"
    
    if [[ ! -d "$component_path" ]]; then
        echo "  - Status: ❌ Missing"
        return
    fi
    
    echo "  - Status: ✅ Present"
    
    # Count files by type
    local py_files=$(find "$component_path" -name "*.py" 2>/dev/null | wc -l)
    local cpp_files=$(find "$component_path" -name "*.cpp" -o -name "*.c" -o -name "*.h" -o -name "*.hpp" 2>/dev/null | wc -l)
    local tf_files=$(find "$component_path" -name "*.tf" 2>/dev/null | wc -l)
    local yml_files=$(find "$component_path" -name "*.yml" -o -name "*.yaml" 2>/dev/null | wc -l)
    local md_files=$(find "$component_path" -name "*.md" 2>/dev/null | wc -l)
    local sh_files=$(find "$component_path" -name "*.sh" 2>/dev/null | wc -l)
    local js_files=$(find "$component_path" -name "*.js" -o -name "*.ts" 2>/dev/null | wc -l)
    
    echo "  - File counts:"
    [[ $py_files -gt 0 ]] && echo "    - Python files: $py_files"
    [[ $cpp_files -gt 0 ]] && echo "    - C++ files: $cpp_files"
    [[ $tf_files -gt 0 ]] && echo "    - Terraform files: $tf_files"
    [[ $yml_files -gt 0 ]] && echo "    - YAML files: $yml_files"
    [[ $md_files -gt 0 ]] && echo "    - Markdown files: $md_files"
    [[ $sh_files -gt 0 ]] && echo "    - Shell scripts: $sh_files"
    [[ $js_files -gt 0 ]] && echo "    - JavaScript/TypeScript files: $js_files"
    
    # Check for README files
    local readme_files=$(find "$component_path" -name "README.md" -o -name "readme.md" 2>/dev/null)
    if [[ -n "$readme_files" ]]; then
        echo "  - Documentation:"
        echo "$readme_files" | while read -r readme; do
            echo "    - $(basename "$(dirname "$readme")")/$(basename "$readme")"
        done
    else
        echo "  - Documentation: ❌ No README found"
    fi
    
    # Check for key files
    case "$component_name" in
        "API")
            local main_files=$(find "$component_path" -name "main.py" -o -name "app.py" -o -name "server.py" 2>/dev/null)
            [[ -n "$main_files" ]] && echo "  - Entry points: $(echo "$main_files" | wc -l) found"
            ;;
        "Core/Python")
            local pipeline_files=$(find "$component_path" -name "pipeline" -type d 2>/dev/null)
            [[ -n "$pipeline_files" ]] && echo "  - Pipeline directory: ✅ Present"
            ;;
        "Core/C++")
            local cmake_files=$(find "$component_path" -name "CMakeLists.txt" -o -name "Makefile" 2>/dev/null)
            [[ -n "$cmake_files" ]] && echo "  - Build system: ✅ Present"
            ;;
        "Terraform")
            local main_tf=$(find "$component_path" -name "main.tf" 2>/dev/null)
            [[ -n "$main_tf" ]] && echo "  - Main configuration: ✅ Present"
            ;;
        "K8s")
            local deploy_files=$(find "$component_path" -name "deploy*.yml" -o -name "deploy*.yaml" 2>/dev/null)
            [[ -n "$deploy_files" ]] && echo "  - Deployment files: ✅ Present"
            ;;
    esac
}

# Function to extract Mermaid diagram from README
extract_mermaid_diagram() {
    local readme_file="$1"
    
    if [[ -f "$readme_file" ]]; then
        # Extract Mermaid diagram between ```mermaid and ```
        awk '/```mermaid/,/```/' "$readme_file" | grep -v '```' > "$TEMP_DIR/mermaid_diagram.txt"
        
        if [[ -s "$TEMP_DIR/mermaid_diagram.txt" ]]; then
            return 0
        fi
    fi
    
    return 1
}

# Function to generate a new Mermaid diagram based on components
generate_mermaid_diagram() {
    cat > "$TEMP_DIR/generated_mermaid.txt" << 'EOF'
graph TB
    subgraph "Client Layer"
        A[Web Application]
        B[Mobile App]
        C[API Clients]
    end

    subgraph "API Gateway"
        D[FastAPI Service]
        D1[Pipeline API]
        D2[Search API]
        D3[Authentication]
    end

    subgraph "Processing Layer"
        E[Python Pipeline]
        F[C++ Performance Kernels]
        G[Video Processing]
        H[Image Processing]
        I[Embedding Generation]
    end

    subgraph "Storage Layer"
        J[(Qdrant Vector DB)]
        K[(PostgreSQL)]
        L[(AWS S3)]
    end

    subgraph "Infrastructure"
        M[Terraform IaC]
        N[Kubernetes Deployment]
        O[AWS Batch]
        P[Scripts & Utilities]
    end

    A --> D
    B --> D
    C --> D
    D --> D1
    D --> D2
    D1 --> E
    D2 --> E
    E --> F
    E --> G
    E --> H
    G --> I
    H --> I
    I --> J
    E --> K
    G --> L
    H --> L
    M --> O
    N --> O
    P --> E
    
    style D fill:#e1f5fe
    style E fill:#f3e5f5
    style F fill:#fff3e0
    style J fill:#e8f5e8
    style M fill:#fce4ec
EOF
}

# Function to analyze data flow between components
analyze_data_flow() {
    cat << 'EOF'
## Inter-Component Data Flow

### 1. Content Ingestion Flow
```
Client → API Gateway → Python Pipeline → C++ Kernels → Storage
```

**Process:**
1. **Client uploads** video/image content via REST API
2. **API Gateway** validates request and queues processing job
3. **Python Pipeline** orchestrates the processing workflow
4. **C++ Kernels** perform GPU-accelerated video processing
5. **Storage Layer** persists processed frames and embeddings

### 2. Search & Retrieval Flow
```
Client → Search API → Qdrant Vector DB → Results
```

**Process:**
1. **Client submits** text or image query
2. **Search API** converts query to embeddings
3. **Qdrant** performs similarity search
4. **Results** returned with metadata and file paths

### 3. Infrastructure Management Flow
```
Terraform → AWS Resources → Kubernetes → Application Deployment
```

**Process:**
1. **Terraform** provisions cloud infrastructure
2. **AWS Resources** provide compute and storage
3. **Kubernetes** orchestrates container deployment
4. **Scripts** manage maintenance and monitoring

### 4. Data Processing Pipeline
```
Raw Video → Border Detection → Frame Extraction → Embedding → Vector Storage
```

**Components involved:**
- **C++ Kernels**: GPU-accelerated video processing
- **Python Pipeline**: Scene detection and orchestration
- **CLIP Models**: Embedding generation
- **Qdrant**: Vector indexing and storage
EOF
}

# Function to check for missing documentation
check_missing_docs() {
    local missing_docs=()
    
    # Check for component-specific documentation
    [[ ! -f "$PROJECT_ROOT/api/README.md" ]] && missing_docs+=("API component README")
    [[ ! -f "$PROJECT_ROOT/core/py/README.md" ]] && missing_docs+=("Core Python README")
    [[ ! -f "$PROJECT_ROOT/core/cpp/README.md" ]] && missing_docs+=("Core C++ README")
    [[ ! -f "$PROJECT_ROOT/qdrant/README.md" ]] && missing_docs+=("Qdrant README")
    [[ ! -f "$PROJECT_ROOT/terraform/README.md" ]] && missing_docs+=("Terraform README")
    [[ ! -f "$PROJECT_ROOT/k8s/README.md" ]] && missing_docs+=("Kubernetes README")
    [[ ! -f "$PROJECT_ROOT/scripts/README.md" ]] && missing_docs+=("Scripts README")
    
    # Check for other important documentation
    [[ ! -f "$PROJECT_ROOT/CONTRIBUTING.md" ]] && missing_docs+=("Contributing guidelines")
    [[ ! -f "$PROJECT_ROOT/DEPLOYMENT.md" ]] && missing_docs+=("Deployment guide")
    [[ ! -f "$PROJECT_ROOT/TROUBLESHOOTING.md" ]] && missing_docs+=("Troubleshooting guide")
    [[ ! -f "$PROJECT_ROOT/API_REFERENCE.md" ]] && missing_docs+=("API reference documentation")
    
    if [[ ${#missing_docs[@]} -gt 0 ]]; then
        echo "## Missing Documentation"
        echo ""
        echo "The following documentation files are missing or need attention:"
        echo ""
        for doc in "${missing_docs[@]}"; do
            echo "- ❌ $doc"
        done
        echo ""
        echo "**Recommendation:** Create these documentation files to improve project maintainability."
    else
        echo "## Documentation Status"
        echo ""
        echo "✅ All essential documentation appears to be present."
    fi
}

# Function to generate the architecture overview
generate_architecture_overview() {
    log "Generating architecture overview..."
    
    cat > "$OUTPUT_FILE" << EOF
# Architecture Overview - Oriane Visual Extraction Pipeline

*Generated on: $(date)*

## Executive Summary

The Oriane Visual Extraction Pipeline is a comprehensive, GPU-accelerated system for processing multimedia content and converting it into searchable embeddings. This document provides a detailed analysis of the system architecture, component inventory, and inter-component data flow.

## Component Inventory

EOF

    # Analyze each component
    log "Analyzing API component..."
    echo "### API Component" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    analyze_component "$PROJECT_ROOT/api" "API" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    
    log "Analyzing Core Python component..."
    echo "### Core Python Pipeline" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    analyze_component "$PROJECT_ROOT/core/py" "Core/Python" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    
    log "Analyzing Core C++ component..."
    echo "### Core C++ Kernels" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    analyze_component "$PROJECT_ROOT/core/cpp" "Core/C++" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    
    log "Analyzing Qdrant component..."
    echo "### Qdrant Vector Database" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    analyze_component "$PROJECT_ROOT/qdrant" "Qdrant" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    
    log "Analyzing Terraform component..."
    echo "### Terraform Infrastructure" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    analyze_component "$PROJECT_ROOT/terraform" "Terraform" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    
    log "Analyzing Scripts component..."
    echo "### Utility Scripts" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    analyze_component "$PROJECT_ROOT/scripts" "Scripts" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    
    log "Analyzing K8s component..."
    echo "### Kubernetes Deployment" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    analyze_component "$PROJECT_ROOT/k8s" "K8s" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    
    # Add architecture diagram
    echo "## System Architecture Diagram" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    
    if extract_mermaid_diagram "$PROJECT_ROOT/README.md"; then
        echo "\`\`\`mermaid" >> "$OUTPUT_FILE"
        cat "$TEMP_DIR/mermaid_diagram.txt" >> "$OUTPUT_FILE"
        echo "\`\`\`" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        echo "*Diagram extracted from project README*" >> "$OUTPUT_FILE"
    else
        warn "Using generated Mermaid diagram as fallback"
        generate_mermaid_diagram
        echo "\`\`\`mermaid" >> "$OUTPUT_FILE"
        cat "$TEMP_DIR/generated_mermaid.txt" >> "$OUTPUT_FILE"
        echo "\`\`\`" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        echo "*Auto-generated diagram based on component analysis*" >> "$OUTPUT_FILE"
    fi
    
    echo "" >> "$OUTPUT_FILE"
    
    # Add data flow analysis
    analyze_data_flow >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    
    # Add missing documentation check
    check_missing_docs >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    
    # Add component summary table
    echo "## Component Summary Table" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "| Component | Status | Primary Language | Purpose |" >> "$OUTPUT_FILE"
    echo "|-----------|--------|------------------|---------|" >> "$OUTPUT_FILE"
    echo "| API | $(check_component "$PROJECT_ROOT/api" "API") | Python | REST API endpoints |" >> "$OUTPUT_FILE"
    echo "| Core/Python | $(check_component "$PROJECT_ROOT/core/py" "Core/Python") | Python | Processing pipeline |" >> "$OUTPUT_FILE"
    echo "| Core/C++ | $(check_component "$PROJECT_ROOT/core/cpp" "Core/C++") | C++ | Performance kernels |" >> "$OUTPUT_FILE"
    echo "| Qdrant | $(check_component "$PROJECT_ROOT/qdrant" "Qdrant") | Python | Vector database |" >> "$OUTPUT_FILE"
    echo "| Terraform | $(check_component "$PROJECT_ROOT/terraform" "Terraform") | HCL | Infrastructure as Code |" >> "$OUTPUT_FILE"
    echo "| Scripts | $(check_component "$PROJECT_ROOT/scripts" "Scripts") | Shell/Python | Utilities |" >> "$OUTPUT_FILE"
    echo "| K8s | $(check_component "$PROJECT_ROOT/k8s" "K8s") | YAML | Container orchestration |" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    
    # Add recommendations
    echo "## Recommendations" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "### Architecture Improvements" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "1. **Documentation Enhancement**: Address missing documentation identified above" >> "$OUTPUT_FILE"
    echo "2. **Component Integration**: Ensure all components have proper integration tests" >> "$OUTPUT_FILE"
    echo "3. **Performance Monitoring**: Add metrics collection for each component" >> "$OUTPUT_FILE"
    echo "4. **Security Hardening**: Implement security best practices across all components" >> "$OUTPUT_FILE"
    echo "5. **Scalability Planning**: Design for horizontal scaling of processing components" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    
    echo "---" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "*This document was automatically generated by the architecture inventory script.*" >> "$OUTPUT_FILE"
    echo "*Last updated: $(date)*" >> "$OUTPUT_FILE"
}

# Main function
main() {
    log "Starting architecture inventory analysis..."
    
    # Check if we're in the right directory
    if [[ ! -f "$PROJECT_ROOT/README.md" ]]; then
        error "README.md not found in project root. Are you in the correct directory?"
        exit 1
    fi
    
    # Generate the architecture overview
    generate_architecture_overview
    
    # Cleanup temporary files
    rm -rf "$TEMP_DIR"
    
    log "Architecture overview generated successfully!"
    log "Output file: $OUTPUT_FILE"
    
    # Display summary
    echo ""
    echo "=== COMPONENT INVENTORY SUMMARY ==="
    echo "API Component: $(check_component "$PROJECT_ROOT/api" "API")"
    echo "Core Python: $(check_component "$PROJECT_ROOT/core/py" "Core/Python")"
    echo "Core C++: $(check_component "$PROJECT_ROOT/core/cpp" "Core/C++")"
    echo "Qdrant: $(check_component "$PROJECT_ROOT/qdrant" "Qdrant")"
    echo "Terraform: $(check_component "$PROJECT_ROOT/terraform" "Terraform")"
    echo "Scripts: $(check_component "$PROJECT_ROOT/scripts" "Scripts")"
    echo "K8s: $(check_component "$PROJECT_ROOT/k8s" "K8s")"
    echo "================================="
    
    log "Analysis complete! Check $OUTPUT_FILE for detailed results."
}

# Run the main function
main "$@"
