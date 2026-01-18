#!/bin/bash

# Usage: ./zip_experiments.sh experiment_logs/experiment_20260111_070543_seed42.txt

LOG_FILE="$1"
SEARCH_DIR="src/tests/output"
OUTPUT_DIR="experiment_zips"

if [ ! -f "$LOG_FILE" ]; then
    echo "Error: File $LOG_FILE not found."
    exit 1
fi

LOG_FILENAME=$(basename -- "$LOG_FILE")
FILENAME_NO_EXT="${LOG_FILENAME%.*}"

mkdir -p "$OUTPUT_DIR"
OUTPUT_ZIP="$OUTPUT_DIR/${FILENAME_NO_EXT}.zip"

# Extract Reference Date from Log Filename
if [[ "$FILENAME_NO_EXT" =~ ([0-9]{8})_([0-9]{6}) ]]; then
    REF_DATE_STR="${BASH_REMATCH[1]}${BASH_REMATCH[2]}"
    echo "Processing $LOG_FILENAME"
    echo "Reference Date: $REF_DATE_STR"
else
    echo "Error: Could not extract YYYYMMDD_HHMMSS from filename."
    exit 1
fi

FILES_TO_ZIP=()

while IFS=, read -r JOB_NAME JOB_ID STATUS; do
    [[ "$JOB_NAME" =~ ^#.*$ ]] || [[ -z "$JOB_NAME" ]] && continue

    MATCHES=( "$SEARCH_DIR"/*_"$JOB_NAME" )
    
    BEST_FOLDER=""
    BEST_DATE_STR=""

    for FOLDER in "${MATCHES[@]}"; do
        [ -e "$FOLDER" ] || continue
        
        FOLDER_NAME=$(basename "$FOLDER")
        
        # Extract Timestamp part
        TS_PART=$(echo "$FOLDER_NAME" | cut -d'_' -f1)
        
        # FIX: Use sed instead of tr to remove T, -, and :
        FOLDER_DATE_STR=$(echo "$TS_PART" | sed 's/[-T:]//g')
        
        [[ ! "$FOLDER_DATE_STR" =~ ^[0-9]{14}$ ]] && continue

        if [[ "$FOLDER_DATE_STR" > "$REF_DATE_STR" ]]; then
            if [[ -z "$BEST_DATE_STR" ]] || [[ "$FOLDER_DATE_STR" < "$BEST_DATE_STR" ]]; then
                BEST_FOLDER="$FOLDER"
                BEST_DATE_STR="$FOLDER_DATE_STR"
            fi
        fi
    done

    if [[ -n "$BEST_FOLDER" ]]; then
        FILES_TO_ZIP+=("$BEST_FOLDER")
    else
        echo "Warning: No valid match found newer than ref date for $JOB_NAME"
    fi

done < "$LOG_FILE"

if [ ${#FILES_TO_ZIP[@]} -gt 0 ]; then
    zip -r -q "$OUTPUT_ZIP" "${FILES_TO_ZIP[@]}"
    echo "Success! Created: $OUTPUT_ZIP"
else
    echo "No folders found matching criteria. Zip not created."
fi