#!/bin/bash

mkdir -p artifacts
echo "$DIFF_FILES" > artifacts/diff_files.txt

if [ -z "$DIFF_FILES" ]; then
    echo "No changed files"
    exit 0
fi

echo "Changed files"
echo "$DIFF_FILES"


# Check for spaces in packages
PACKAGES_WITH_SPACES=$(echo "$DIFF_FILES" | egrep '^?\s+packages\/[^/]* [^/]*/.*$' )

if [ ! -z "$PACKAGES_WITH_SPACES" ]; then
    echo "Spaces are not allowed in package names"
    exit 1
fi


# Don't allow deleted package files
DELETED_METADATA_FILES=$(echo "$DIFF_FILES" | egrep '^D\s+packages\/[^\/]*\/metadata.json$' )

if [ ! -z "$DELETED_METADATA_FILES" ]; then
    echo "Deleting package metadata files is not allowed, to delist a package remove all versions."
    exit 1
fi


# Download schema file
if [ -z "$SCHEMA_URL" ]; then
    SCHEMA_URL="https://gitlab.com/kicad/code/kicad/-/raw/master/kicad/pcm/schemas/pcm.v1.schema.json"
fi

curl -s -S -L "$SCHEMA_URL" -o schema.json
CURL_RETURN=$?

if [ $CURL_RETURN -ne 0 ]; then
    echo "Failed to download schema, curl returned $CURL_RETURN"
    exit 1
fi

# Validate new packages
NEW_METADATA_FILES=$(echo "$DIFF_FILES" | egrep '^A\s+packages\/[^\/]*\/metadata.json$' | awk '{print $2}')

for f in $NEW_METADATA_FILES; do
    PACKAGE=$(echo "$f" | awk -F'/' '{print $2}')
    echo "Validating new package $PACKAGE"
    python3 "ci/validate-package.py" "$PACKAGE" "$f"
    if [ $? -ne 0 ]; then
        echo "Validation of package $PACKAGE failed"
        exit 1
    fi
done


# Validate changed packages
CHANGED_METADATA_FILES=$(echo "$DIFF_FILES" | egrep '^M\s+packages\/[^\/]*\/metadata.json$' | awk '{print $2}')

for f in $CHANGED_METADATA_FILES; do
    PACKAGE=$(echo "$f" | awk -F'/' '{print $2}')
    echo "Validating changes to package $PACKAGE"
    git show "$MERGE_BASE_SHA:$f" > "$f".old
    python3 "ci/validate-package.py" "$PACKAGE" "$f" "$f".old
    if [ $? -ne 0 ]; then
        echo "Validation of package $PACKAGE failed"
        exit 1
    fi
done


# Validate icon files
ICON_FILES=$(echo "$DIFF_FILES" | egrep '^[MA]\s+packages\/[^\/]*\/icon.png$' | awk '{print $2}')

for f in $ICON_FILES; do
    echo "Validating icon $f"
    PACKAGE=$(echo "$f" | awk -F'/' '{print $2}')
    python3 "ci/validate-image.py" "$f"
    if [ $? -ne 0 ]; then
        echo "Validation of icon for package $PACKAGE failed"
        exit 1
    fi
done

echo "Done"
