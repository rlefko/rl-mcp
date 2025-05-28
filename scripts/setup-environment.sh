#!/bin/bash

# ===============================
# Script: setup_environment.sh
# Description: Sets up the development environment with Homebrew/Chocolatey, Python, virtualenv, Docker, and dependencies.
# ===============================

# ===============================
# Configuration Variables
# ===============================
PYTHON_VERSION="3.12"

# ===============================
# Color Definitions
# ===============================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
GREY='\033[90m'
NC='\033[0m' # No Color

# ===============================
# Emoji Definitions
# ===============================
SUCCESS_EMOJI="✅"
WARNING_EMOJI="⚠️"
ERROR_EMOJI="❌"
DOCKER_EMOJI="🐳"
PYTHON_EMOJI="🐍"
VENV_EMOJI="🔧"
HOME_EMOJI="🏠"
SETUP_EMOJI="🚀"
BUILD_EMOJI="🛠️"

# ===============================
# Utility Functions
# ===============================

# Function to log messages with emoji and color
log() {
    local color=$1
    local emoji=$2
    local message=$3
    echo -e "${color}${emoji} ${message}${NC}"
}

# Function to display a spinner for long-running tasks
spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏' # Using Braille patterns for a smoother spinner
    local i=0
    while kill -0 "$pid" 2>/dev/null; do
        local temp=${spinstr:i++%${#spinstr}:1}
        printf " ${BLUE}[%s]${NC}" "$temp"
        sleep $delay
        printf "\r"
    done
    printf "    \r"
}

# Function to exit with error
error_exit() {
    log $RED "$ERROR_EMOJI $1"
    exit 1
}

# ===============================
# System Compatibility and Package Managers
# ===============================

check_system() {
    log $BLUE "Checking system compatibility..."

    OS_TYPE=""
    PACKAGE_MANAGER=""

    case "$OSTYPE" in
        darwin*)  
            OS_TYPE="macOS"
            PACKAGE_MANAGER="brew"
            ;;
        linux-gnu*)
            OS_TYPE="Linux"
            # Detect Linux distribution
            if [ -x "$(command -v apt)" ]; then
                PACKAGE_MANAGER="apt"
            elif [ -x "$(command -v dnf)" ]; then
                PACKAGE_MANAGER="dnf"
            elif [ -x "$(command -v brew)" ]; then
                PACKAGE_MANAGER="brew"
            else
                error_exit "Unsupported Linux distribution. Please install Homebrew or use a supported package manager."
            fi
            ;;
        msys*|cygwin*|win32*)
            OS_TYPE="Windows"
            PACKAGE_MANAGER="choco"
            ;;
        *)
            error_exit "Unsupported OS: $OSTYPE"
            ;;
    esac

    log $GREEN "$SUCCESS_EMOJI Detected OS: $OS_TYPE with package manager: $PACKAGE_MANAGER."
}

# Function to install Homebrew (for Linux if not installed)
install_homebrew() {
    if [ "$PACKAGE_MANAGER" == "brew" ]; then
        if ! command -v brew &> /dev/null; then
            log $YELLOW "$WARNING_EMOJI Homebrew not found. Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" & 
            spinner $!
            echo
            # Detect brew installation path
            BREW_PREFIX=$(brew --prefix 2>/dev/null)
            if [ -z "$BREW_PREFIX" ]; then
                if [ -x "/opt/homebrew/bin/brew" ]; then
                    BREW_PREFIX="/opt/homebrew"
                elif [ -x "/home/linuxbrew/.linuxbrew/bin/brew" ]; then
                    BREW_PREFIX="/home/linuxbrew/.linuxbrew"
                else
                    error_exit "Failed to locate Homebrew after installation."
                fi
            fi

            # Add Homebrew to PATH in current shell
            eval "$("$BREW_PREFIX/bin/brew" shellenv)"

            if command -v brew &> /dev/null; then
                log $GREEN "$SUCCESS_EMOJI Homebrew installed successfully."
            else
                error_exit "Failed to install Homebrew."
            fi
        else
            log $GREEN "$SUCCESS_EMOJI Homebrew is already installed."
        fi
    fi
}

# Function to install Chocolatey (for Windows if not installed)
install_chocolatey() {
    if [ "$PACKAGE_MANAGER" == "choco" ]; then
        if ! command -v choco &> /dev/null; then
            log $YELLOW "$WARNING_EMOJI Chocolatey not found. Installing Chocolatey..."
            # Note: Requires administrator privileges
            SETUP_CMD='Set-ExecutionPolicy Bypass -Scope Process -Force; \
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; \
iex ((New-Object System.Net.WebClient).DownloadString("https://chocolatey.org/install.ps1"))'

            # Execute the PowerShell command
            powershell.exe -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "$SETUP_CMD" & 
            spinner $!
            echo

            if command -v choco &> /dev/null; then
                log $GREEN "$SUCCESS_EMOJI Chocolatey installed successfully."
            else
                error_exit "Failed to install Chocolatey."
            fi
        else
            log $GREEN "$SUCCESS_EMOJI Chocolatey is already installed."
        fi
    fi
}

# Function to install packages using the detected package manager
install_package() {
    local package=$1
    local install_cmd

    case "$PACKAGE_MANAGER" in
        brew)
            # Skip auto-update by setting HOMEBREW_NO_AUTO_UPDATE=1
            export HOMEBREW_NO_AUTO_UPDATE=1
            install_cmd="brew install $package"
            ;;
        apt)
            install_cmd="sudo apt-get install -y $package"
            ;;
        dnf)
            install_cmd="sudo dnf install -y $package"
            ;;
        choco)
            # Skip auto-update by adding --no-auto-update
            install_cmd="choco install $package -y --no-auto-update"
            ;;
        *)
            error_exit "Unsupported package manager: $PACKAGE_MANAGER"
            ;;
    esac

    log $BLUE "Installing $package..."
    $install_cmd & 
    spinner $!
    echo

    if command -v $package &> /dev/null || { [ "$PACKAGE_MANAGER" == "choco" ] && [ "$package" == "docker-desktop" ]; }; then
        # Special case for docker-desktop which might not be in PATH
        log $GREEN "$SUCCESS_EMOJI $package installed successfully."
    else
        error_exit "Failed to install $package."
    fi
}

# ===============================
# Docker Installation and Setup
# ===============================

install_docker() {
    log $BLUE "$DOCKER_EMOJI Checking Docker installation..."

    if ! command -v docker &> /dev/null; then
        log $YELLOW "$WARNING_EMOJI Docker not found. Installing Docker..."

        case "$OS_TYPE" in
            macOS)
                # Attempt to install Docker via Homebrew
                install_package "docker"
                log $BLUE "$DOCKER_EMOJI Launching Docker Desktop..."
                open -a Docker || {
                    log $YELLOW "$WARNING_EMOJI Failed to launch Docker Desktop automatically."
                    log $BLUE "Please install Docker Desktop manually from https://www.docker.com/products/docker-desktop"
                }
                ;;
            Linux)
                if [ "$PACKAGE_MANAGER" == "apt" ]; then
                    sudo apt-get install -y ca-certificates curl gnupg lsb-release
                    sudo mkdir -p /etc/apt/keyrings
                    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
                    echo \
                      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
                      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
                    sudo apt-get update
                    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
                elif [ "$PACKAGE_MANAGER" == "dnf" ]; then
                    sudo dnf -y install dnf-plugins-core
                    sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
                    sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
                    sudo systemctl start docker
                    sudo systemctl enable docker
                elif [ "$PACKAGE_MANAGER" == "brew" ]; then
                    install_package "docker"
                    log $BLUE "$DOCKER_EMOJI Launching Docker Desktop..."
                    open /Applications/Docker.app || {
                        log $YELLOW "$WARNING_EMOJI Failed to launch Docker."
                        log $BLUE "Please ensure Docker is installed and run Docker Desktop manually."
                    }
                fi
                ;;
            Windows)
                # Attempt to install Docker Desktop via Chocolatey
                install_package "docker-desktop"
                log $BLUE "$DOCKER_EMOJI Launching Docker Desktop..."
                start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe" || {
                    log $YELLOW "$WARNING_EMOJI Failed to launch Docker Desktop automatically."
                    log $BLUE "Please install Docker Desktop manually from https://www.docker.com/products/docker-desktop"
                }
                ;;
            *)
                error_exit "Unsupported OS for Docker installation."
                ;;
        esac

        # Wait for Docker daemon to start
        log $BLUE "$DOCKER_EMOJI Waiting for Docker daemon to start..."

        if [ "$OS_TYPE" == "macOS" ] || [ "$OS_TYPE" == "Windows" ]; then
            # For macOS and Windows, manual installation is likely required
            log $BLUE "Please ensure Docker Desktop is installed and running."
            log $BLUE "If you installed Docker manually, please start Docker Desktop now."
            while ! docker info > /dev/null 2>&1; do
                sleep 2
            done
        else
            # For Linux, assume Docker starts automatically or use systemctl
            while ! docker info > /dev/null 2>&1; do
                sleep 2
            done
        fi

        log $GREEN "$SUCCESS_EMOJI Docker is installed and the daemon is running."
    else
        log $GREEN "$SUCCESS_EMOJI Docker is already installed."
    fi
}

# ===============================
# Python and Virtual Environment Setup
# ===============================

install_python() {
    PYTHON_EXECUTABLE="python${PYTHON_VERSION}"
    log $BLUE "$PYTHON_EMOJI Checking for Python $PYTHON_VERSION..."

    if command -v $PYTHON_EXECUTABLE &> /dev/null; then
        log $GREEN "$SUCCESS_EMOJI Python $PYTHON_VERSION is already installed."
    else
        log $YELLOW "$WARNING_EMOJI Python $PYTHON_VERSION not found. Installing Python $PYTHON_VERSION..."
        if [ "$PACKAGE_MANAGER" == "brew" ] || [ "$PACKAGE_MANAGER" == "choco" ]; then
            install_package "python@$PYTHON_VERSION"
        elif [ "$PACKAGE_MANAGER" == "apt" ] || [ "$PACKAGE_MANAGER" == "dnf" ]; then
            install_package "python${PYTHON_VERSION}"
        fi

        # Verify Python installation
        if command -v $PYTHON_EXECUTABLE &> /dev/null; then
            log $GREEN "$SUCCESS_EMOJI Python $PYTHON_VERSION installed successfully."
        else
            error_exit "Python $PYTHON_VERSION installation verification failed."
        fi
    fi
}

handle_virtualenv() {
    local VENV_DIR="venv"

    log $BLUE "$VENV_EMOJI Setting up virtual environment..."

    # Check if Python executable exists
    PYTHON_EXECUTABLE="python${PYTHON_VERSION}"
    if ! command -v $PYTHON_EXECUTABLE &> /dev/null; then
        error_exit "Python executable $PYTHON_EXECUTABLE not found. Cannot create virtual environment."
    fi

    # Remove existing virtual environment if necessary
    if [ -d "$VENV_DIR" ]; then
        log $YELLOW "$WARNING_EMOJI Existing virtual environment detected. Removing..."
        rm -rf "$VENV_DIR" || error_exit "Failed to remove existing virtual environment."
    fi

    # Create a new virtual environment
    log $BLUE "$VENV_EMOJI Creating a new virtual environment in '$VENV_DIR'..."
    $PYTHON_EXECUTABLE -m venv "$VENV_DIR" || error_exit "Failed to create virtual environment."

    if [ -d "$VENV_DIR" ]; then
        log $GREEN "$SUCCESS_EMOJI Virtual environment created successfully."
    else
        error_exit "Virtual environment directory not found after creation."
    fi

    # Activate the virtual environment
    log $BLUE "$VENV_EMOJI Activating the virtual environment..."
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate" || error_exit "Failed to activate virtual environment."

    if [ "$VIRTUAL_ENV" != "" ]; then
        log $GREEN "$SUCCESS_EMOJI Virtual environment activated."
    else
        error_exit "Virtual environment activation failed."
    fi
}

install_pre_commit() {
    log $BLUE "$SETUP_EMOJI Installing pre-commit hooks..."

    install_package "pre-commit"

    if [ -f ".pre-commit-config.yaml" ]; then
        # Run pre-commit install
        pre-commit install
        log $GREEN "$SUCCESS_EMOJI Pre-commit hooks installed successfully!"
    else
        log $YELLOW "$WARNING_EMOJI .pre-commit-config.yaml not found. Skipping pre-commit installation."
    fi
}

install_jq() {
    log $BLUE "$SETUP_EMOJI Installing jq..."

    install_package "jq"
}

install_github_cli() {
    log $BLUE "$SETUP_EMOJI Installing GitHub CLI..."
    
    case "$OS_TYPE" in
        macOS)
            install_package "gh"
            ;;
        Linux)
            if [ "$PACKAGE_MANAGER" == "apt" ]; then
                curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
                sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
                echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
                sudo apt update
                sudo apt install gh -y
            elif [ "$PACKAGE_MANAGER" == "dnf" ]; then
                sudo dnf install 'dnf-command(config-manager)' -y
                sudo dnf config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo
                sudo dnf install gh -y
            elif [ "$PACKAGE_MANAGER" == "brew" ]; then
                install_package "gh"
            fi
            ;;
        Windows)
            choco install gh -y
            ;;
        *)
            error_exit "Unsupported OS for GitHub CLI installation."
            ;;
    esac
    
    if command -v gh &> /dev/null; then
        log $GREEN "$SUCCESS_EMOJI GitHub CLI installed successfully."
    else
        error_exit "Failed to install GitHub CLI."
    fi
}

# ===============================
# Install Python Dependencies
# ===============================

install_requirements() {
    if [ -f "requirements.txt" ]; then
        # Log the initial message
        log $BLUE "$SETUP_EMOJI Installing Python packages from requirements.txt..."

        # Array to hold pip output lines
        output_lines=()

        # Run pip install and process output to show only the last 5 lines in grey
        pip install -r requirements.txt 2>&1 | while read -r line; do
            # Append each new line to the array
            output_lines+=("$line")

            # Keep only the last 5 lines in the array
            if [ "${#output_lines[@]}" -gt 5 ]; then
                output_lines=("${output_lines[@]:1}")
            fi

            # Save cursor position and clear below the current line
            tput sc
            tput cud 1
            tput ed

            # Print each line in grey, truncating to fit within a single line
            for output_line in "${output_lines[@]}"; do
                printf "\033[90m%.80s\033[0m\n" "$output_line"  # Truncate each line to 80 characters
            done

            # Fill in remaining lines to maintain consistent 5-line display
            for ((i=${#output_lines[@]}; i<5; i++)); do
                echo
            done

            # Restore cursor to spinner line
            tput rc
        done

        # Move down to the next line after the pip output and clear any remaining content
        tput cud 5 && tput ed

        # Clear spinner and output lines when pip completes
        log $GREEN "$SUCCESS_EMOJI All packages installed successfully!"
    else
        log $YELLOW "$WARNING_EMOJI requirements.txt not found. Skipping Python package installation."
    fi
}

# ===============================
# Main Execution Flow
# ===============================

main() {
    log $HOME_EMOJI " Starting environment setup..."

    check_system
    if [ "$PACKAGE_MANAGER" == "brew" ]; then
        install_homebrew
    elif [ "$PACKAGE_MANAGER" == "choco" ]; then
        install_chocolatey
    fi
    install_docker
    install_github_cli
    install_pre_commit
    install_jq
    install_python
    handle_virtualenv
    install_requirements

    log $GREEN "🎉 Environment setup completed successfully! 🎉"
    log $GREEN "To activate your virtual environment in future sessions, run: source venv/bin/activate"
}

# Run the main function
main
