#!/bin/bash
# Package the call-flow-deep-dive skill into a single archive
# Usage: bash scripts/package_skill.sh [output_dir]
# 
# This bundles SKILL.md + all reference files into a self-contained zip
# that can be copied to any system and installed into ~/.hermes/skills/

set -e

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUT_DIR="${1:-$SKILL_DIR}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PACKAGE_NAME="skill-call-flow-deep-dive_${TIMESTAMP}.zip"
PACKAGE_PATH="${OUTPUT_DIR}/${PACKAGE_NAME}"

cd "$SKILL_DIR"

# Create zip with the skill structure
zip -r "$PACKAGE_PATH" \
    SKILL.md \
    references/extract_html_data.py \
    references/generate_report.py \
    references/generate_html_report.py \
    references/git-submodule-fix.md 2>/dev/null || true

echo "Package created: $PACKAGE_PATH"
echo "Contents:"
unzip -l "$PACKAGE_PATH" | tail -n +4 | head -n -2