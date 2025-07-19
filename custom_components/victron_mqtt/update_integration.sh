#!/bin/bash

# ==== CONFIGURATION ====
GITHUB_USER="tomer-w"
GITHUB_REPO="ha-victron-mqtt"
TARGET_SUBFOLDER="custom_components/victron_mqtt"
DEST_FOLDER="/config/custom_components/victron_mqtt"
# ========================
# Usage:
# Run the script without arguments to update the integration.
# Use the --restart flag to restart Home Assistant after updating.
# Use the --main flag to force using main branch even if releases exist.
# Examples: 
#   bash update_integration.sh --restart
#   bash update_integration.sh --main
#   bash update_integration.sh --main --restart

RESTART_HA=false
USE_MAIN=false

# Parse command line arguments
for arg in "$@"; do
    case $arg in
        --restart)
            RESTART_HA=true
            ;;
        --main)
            USE_MAIN=true
            ;;
    esac
done

# Fetch latest release tag via GitHub API (unless --main flag is used)
if [ "$USE_MAIN" = true ]; then
    echo "🔀 Using main branch as requested (--main flag)"
    LATEST_TAG="null"
else
    LATEST_TAG=$(curl -s "https://api.github.com/repos/$GITHUB_USER/$GITHUB_REPO/releases/latest" | jq -r .tag_name)
fi

if [ "$LATEST_TAG" == "null" ] || [ -z "$LATEST_TAG" ]; then
    if [ "$USE_MAIN" = true ]; then
        echo "📥 Downloading from main branch"
    else
        echo "⚠️  No releases found. Falling back to main branch."
    fi
    ZIP_URL="https://github.com/$GITHUB_USER/$GITHUB_REPO/archive/refs/heads/main.zip"
    TMP_FOLDER="$GITHUB_REPO-main"
else
    echo "⬇️  Found latest release: $LATEST_TAG"
    ZIP_URL="https://github.com/$GITHUB_USER/$GITHUB_REPO/archive/refs/tags/$LATEST_TAG.zip"
    # Remove 'v' prefix from tag for folder name
    TAG_WITHOUT_V="${LATEST_TAG#v}"
    TMP_FOLDER="$GITHUB_REPO-$TAG_WITHOUT_V"
fi

# Create temp dir
TMP_DIR=$(mktemp -d)
echo "TMP_DIR=$TMP_DIR"
cd "$TMP_DIR" || exit 1

# Download and extract
echo "📦 Downloading from $ZIP_URL"
wget -q "$ZIP_URL" -O latest.zip || curl -L "$ZIP_URL" -o latest.zip
unzip -q latest.zip

# Check if the source directory exists
SOURCE_DIR="$TMP_FOLDER/$TARGET_SUBFOLDER"
if [ ! -d "$SOURCE_DIR" ]; then
    echo "❌ Source directory not found: $SOURCE_DIR"
    echo "Available directories in $TMP_FOLDER:"
    ls -la "$TMP_FOLDER/"
    exit 1
fi

# Copy the integration folder to destination
mkdir -p "$DEST_FOLDER"
cp -r "$TMP_FOLDER/$TARGET_SUBFOLDER/"* "$DEST_FOLDER/"
chmod +x "$DEST_FOLDER/"update_integration.sh
echo "✅ Integration updated at $DEST_FOLDER"

# Cleanup
cd /
rm -rf "$TMP_DIR"

# Restart Home Assistant if requested
if [ "$RESTART_HA" = true ]; then
    echo "🧪 Validating Home Assistant configuration..."
    if ha core check; then
        echo "✅ Configuration is valid."
        echo "🔁 Restarting Home Assistant..."
        ha core restart
        echo "✅ Restart command issued."
    else
        echo "❌ Configuration is invalid. Skipping restart."
        exit 1
    fi
fi