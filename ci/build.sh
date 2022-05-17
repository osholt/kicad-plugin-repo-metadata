#!/bin/bash
DIFF_FILES=$(cat artifacts/diff_files.txt)

METADATA_FILES=$(echo "$DIFF_FILES" | egrep '^[AM]\s+packages\/[^\/]*\/metadata.json$' | awk '{print $2}')
ICON_FILES=$(echo "$DIFF_FILES" | egrep '^[AM]\s+packages\/[^\/]*\/icon.png$' | awk '{print $2}')

# add packages with changed metadata to icons list
for f in $METADATA_FILES; do
    icon="$(dirname $f)/icon.png"
    if [ -f $icon ]; then
        if [[ $ICON_FILES != *"$icon"* ]]; then
            ICON_FILES="$ICON_FILES"$'\n'"$icon"
        fi
    fi
done

# add packages with changed icons to metadata list
for f in $ICON_FILES; do
    metadata="$(dirname $f)/metadata.json"
    if [[ $METADATA_FILES != *"$metadata"* ]]; then
        METADATA_FILES="$METADATA_FILES"$'\n'"$metadata"
    fi
done

# create resources archive
if [ ! -z "$ICON_FILES" ]; then
    cd packages
    echo "$ICON_FILES" | sed 's|packages/||g' | xargs zip -9 "../artifacts/resources.zip"
    cd ..
fi

# create packages and update repo
if [ ! -z "$METADATA_FILES" ]; then
    echo "Generating repo with following packages:"
    echo "$METADATA_FILES" | awk -F'/' '{print $2}'
    echo "$METADATA_FILES" | xargs python3 ci/build-repository.py
fi
