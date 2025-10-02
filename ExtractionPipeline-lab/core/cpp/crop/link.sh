# In your link.sh or terminal
export ORIGINAL_LD_LIBRARY_PATH="$LD_LIBRARY_PATH"

NEW_LD_PATH="/usr/lib/x86_64-linux-gnu" # Prioritize system path with driver libs

OLD_IFS=$IFS
IFS=':'
for path_component in $ORIGINAL_LD_LIBRARY_PATH; do # Iterate over original
    case "$path_component" in
        "/usr/local/cuda/lib64"*) ;;
        "/usr/local/cuda-"*"/lib64"*) ;;
        "/usr/lib/x86_64-linux-gnu"*) ;; # Avoid duplicating if already there
        "") ;;
        *) # Keep other paths (like your /tmp/... paths)
            if [ -z "$NEW_LD_PATH" ]; then
                NEW_LD_PATH="$path_component"
            else
                NEW_LD_PATH="$NEW_LD_PATH:$path_component"
            fi
            ;;
    esac
done
IFS=$OLD_IFS
export LD_LIBRARY_PATH="$NEW_LD_PATH"

echo "Testing with new LD_LIBRARY_PATH: '$LD_LIBRARY_PATH'"
sudo ldconfig
