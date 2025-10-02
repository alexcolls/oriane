#!/usr/bin/env bash
# navigation.sh - Interactive menu navigation with keyboard support

# Interactive menu selection with arrow keys
choose_option() {
    # Usage: choose_option "Option 1" "Option 2" ...
    local opts=("$@")
    local selected=0
    local i key

    # Hide cursor
    tput civis

    # Calculate max width needed for options
    local max_width=0
    for opt in "${opts[@]}"; do
        local len=${#opt}
        ((len > max_width)) && max_width=$len
    done
    ((max_width += 8))  # Add padding for arrows and spaces

    # Create horizontal border line
    local border=""
    for ((i=0; i<max_width+4; i++)); do border+="─"; done

    # Initial display of the menu
    echo
    echo "  ╭$border╮"
    echo "  │  $(tput bold)Select an option:$(tput sgr0)${reset}" "$(printf '%*s' $((max_width-14)) '')│"
    echo "  ├$border┤"
    
    # Save cursor position for menu options
    tput sc

    # Initial render of options
    for i in "${!opts[@]}"; do
        if [[ $i -eq $selected ]]; then
            printf "  │ $(tput bold)▶ %-${max_width}s$(tput sgr0) │\n" "${opts[$i]}"
        else
            printf "  │   %-${max_width}s │\n" "${opts[$i]}"
        fi
    done
    echo "  ╰$border╯"

    while true; do
        # Restore cursor position and redraw options
        tput rc
        for i in "${!opts[@]}"; do
            tput el
            if [[ $i -eq $selected ]]; then
                printf "  │ $(tput bold)▶ %-${max_width}s$(tput sgr0) │\n" "${opts[$i]}"
            else
                printf "  │   %-${max_width}s │\n" "${opts[$i]}"
            fi
        done

        # Read user key (arrow or enter)
        IFS= read -rsn1 key 2>/dev/null || continue

        case "$key" in
            $'\x1b')  # escape sequence
                read -rsn2 -t 0.001 rest 2>/dev/null || { continue; }
                key+="$rest"
                case "$key" in
                    $'\x1b[A')  # up arrow
                        ((selected=selected==0?${#opts[@]}-1:selected-1))
                        ;;
                    $'\x1b[B')  # down arrow
                        ((selected=(selected+1)%${#opts[@]}))
                        ;;
                    $'\x1b[C'|$'\x1b[D')  # right/left arrow (acts like Enter)
                        echo "$selected"
                        tput cnorm
                        echo
                        return
                        ;;
                esac
                ;;
            "")  # Enter
                echo "$selected"
                tput cnorm
                echo
                return
                ;;
            q|Q)  # Allow q/Q to exit
                echo "-1"
                tput cnorm
                echo
                return
                ;;
            *)  # Other keys ignored
                ;;
        esac
    done
}
