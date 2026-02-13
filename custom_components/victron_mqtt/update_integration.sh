#!/bin/bash

# ==== CONFIGURATION ====
GITHUB_USER="tomer-w"
GITHUB_REPO="ha-victron-mqtt"
TARGET_SUBFOLDER="custom_components/victron_mqtt"
DEST_FOLDER="/config/custom_components/victron_mqtt"
# ========================
# Usage:
# Run the script without arguments to update the integration to the latest release.
# Use the --restart flag to restart Home Assistant after updating.
# Use the --main flag to force using main branch even if releases exist.
# Use the --version <tag> flag to download a specific version (e.g., v1.0.0).
# Use the --list-versions flag to list all available versions.
# Examples: 
#   bash update_integration.sh --restart
#   bash update_integration.sh --main
#   bash update_integration.sh --main --restart
#   bash update_integration.sh --version v1.0.0
#   bash update_integration.sh --version v1.0.0 --restart
#   bash update_integration.sh --list-versions

RESTART_HA=false
USE_MAIN=false
SPECIFIC_VERSION=""

# Check for jq; if missing, warn and skip printing commit info when using main
if ! command -v jq >/dev/null 2>&1; then
    echo "⚠️  'jq' not found in PATH. Commit info from GitHub will be skipped. To enable it, install jq."
    JQ_AVAILABLE=false
else
    JQ_AVAILABLE=true
fi

# Parse command line arguments
for arg in "$@"; do
    case $arg in
        --restart)
            RESTART_HA=true
            ;;
        --main)
            USE_MAIN=true
            ;;
        --version)
            # Next argument is the version
            SPECIFIC_VERSION="${@:$((OPTIND+1)):1}"
            shift
            ;;
        --list-versions)
            echo "📋 Fetching available versions from GitHub..."
            if ! command -v jq >/dev/null 2>&1; then
                echo "❌ 'jq' is required to list versions. Please install jq."
                exit 1
            fi
            RELEASES=$(curl -s "https://api.github.com/repos/$GITHUB_USER/$GITHUB_REPO/releases" | jq -r '.[].tag_name' | head -20)
            if [ -z "$RELEASES" ]; then
                echo "❌ Could not fetch releases from GitHub."
                exit 1
            fi
            echo "Available versions:"
            echo "$RELEASES"
            echo ""
            echo "💡 Usage: bash update_integration.sh --version <version-tag>"
            exit 0
            ;;
    esac
done

# Validate that --version and --main are not used together
if [ -n "$SPECIFIC_VERSION" ] && [ "$USE_MAIN" = true ]; then
    echo "❌ Error: Cannot use --version and --main flags together."
    exit 1
fi

# Fetch latest release tag via GitHub API (unless --main flag is used or --version is specified)
if [ -n "$SPECIFIC_VERSION" ]; then
    echo "📌 Using specific version: $SPECIFIC_VERSION"
    LATEST_TAG="$SPECIFIC_VERSION"
elif [ "$USE_MAIN" = true ]; then
    echo "🔀 Using main branch as requested (--main flag)"
    LATEST_TAG="null"
else
    LATEST_TAG=$(curl -s "https://api.github.com/repos/$GITHUB_USER/$GITHUB_REPO/releases/latest" | jq -r '.tag_name // empty')
fi

if [ "$LATEST_TAG" == "null" ] || [ -z "$LATEST_TAG" ]; then
    if [ "$USE_MAIN" = true ]; then
        echo "📥 Downloading from main branch"
    else
        echo "⚠️  No releases found. Falling back to main branch."
    fi
    ZIP_URL="https://github.com/$GITHUB_USER/$GITHUB_REPO/archive/refs/heads/main.zip"
    TMP_FOLDER="$GITHUB_REPO-main"
    # If we're downloading from main, fetch and print the latest commit info
    if [ "$JQ_AVAILABLE" = true ]; then
        echo "🔎 Fetching latest commit info for main..."
        # Query the GitHub commits API for the main branch
        COMMIT_INFO=$(curl -s "https://api.github.com/repos/$GITHUB_USER/$GITHUB_REPO/commits/main")
        if [ -n "$COMMIT_INFO" ] && [ "$(echo "$COMMIT_INFO" | jq -r '.sha // empty')" != "" ]; then
            COMMIT_SHA=$(echo "$COMMIT_INFO" | jq -r '.sha')
            # Show only the first line of the commit message
            COMMIT_MESSAGE=$(echo "$COMMIT_INFO" | jq -r '.commit.message' | head -n1 | tr -d '\r')
            COMMIT_AUTHOR=$(echo "$COMMIT_INFO" | jq -r '.commit.author.name')
            COMMIT_DATE=$(echo "$COMMIT_INFO" | jq -r '.commit.author.date')
            echo "🧾 Latest commit on main: $COMMIT_SHA"
            echo "📝 Message: $COMMIT_MESSAGE"
            echo "👤 Author: $COMMIT_AUTHOR"
            echo "📅 Date: $COMMIT_DATE"
        else
            echo "⚠️  Could not fetch latest commit info from GitHub API."
        fi
    else
        echo "ℹ️  Skipping commit info because 'jq' is not available."
    fi
else
    echo "⬇️  Found version: $LATEST_TAG"
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