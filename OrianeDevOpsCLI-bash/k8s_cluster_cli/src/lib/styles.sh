#!/usr/bin/env bash
# styles.sh - Styling and color definitions for Oriane K8s CLI

# Color definitions
export reset="\e[0m"
export bold="\e[1m"
export cyan="\e[36m"
export yellow="\e[33m"
export green="\e[32m"
export red="\e[31m"
export blue="\e[34m"
export magenta="\e[35m"
export highlight="\e[7m"

# Print functions
print_bold() {
    printf "%b%s%b\n" "$bold" "$1" "$reset"
}

print_cyan() {
    printf "%b%s%b\n" "$cyan" "$1" "$reset"
}

print_yellow() {
    printf "%b%s%b\n" "$yellow" "$1" "$reset"
}

print_green() {
    printf "%b%s%b\n" "$green" "$1" "$reset"
}

print_red() {
    printf "%b%s%b\n" "$red" "$1" "$reset"
}

print_blue() {
    printf "%b%s%b\n" "$blue" "$1" "$reset"
}

print_magenta() {
    printf "%b%s%b\n" "$magenta" "$1" "$reset"
}

# Utility function to pause
pause() {
    tput cnorm  # show cursor
    read -rp $'\nPress Enter to continue...'
    tput civis  # hide cursor again
}
