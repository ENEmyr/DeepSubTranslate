#!/bin/sh

# Resolve absolute path
INPUT_PATH=$(realpath "$1")
SOURCE_LANG=$2
TARGET_LANG=$3
# SOURCE_LANG="${2:-eng}"
# TARGET_LANG="${3:-tha}"

# Check which language arguments were provided
if [ -n "$2" ] && [ -n "$3" ]; then
  echo "📘 Using custom language pair: $SOURCE_LANG ➡ $TARGET_LANG"
  # Run the Docker container
  exec docker run --rm \
    -v "$INPUT_PATH":/input \
    aenemy/deep-subtitle-translator:latest \
    -p /input -s "$SOURCE_LANG" -t "$TARGET_LANG"
elif [ -n "$2" ] && [ -z "$3" ]; then
  echo "📘 Using custom source language: $SOURCE_LANG (target default: tha)"
  exec docker run --rm \
    -v "$INPUT_PATH":/input \
    aenemy/deep-subtitle-translator:latest \
    -p /input -s "$SOURCE_LANG"
elif [ -z "$2" ] && [ -n "$3" ]; then
  echo "📘 Using custom target language: $TARGET_LANG (source default: eng)"
  exec docker run --rm \
    -v "$INPUT_PATH":/input \
    aenemy/deep-subtitle-translator:latest \
    -p /input -t "$TARGET_LANG"
else
  echo "📘 Using default language pair: eng ➡ tha"
  exec docker run --rm \
    -v "$INPUT_PATH":/input \
    aenemy/deep-subtitle-translator:latest \
    -p /input
fi
