# FFmpeg Scene Detection Tests

This directory contains test scripts for scene detection functionality using FFmpeg.

## Purpose

These scripts are designed to test and validate the scene detection capabilities of the VideoFramesSceneExtractor lambda function, which uses FFmpeg to analyze video content and detect scene changes.

## Scripts

### 1. extract_frames.py

Extracts frames from videos using FFmpeg's scene detection capabilities.

**Features:**

- Extracts frames at scene changes using FFmpeg
- Filters out blank frames
- Ensures minimum number of frames per video
- Names frames with sequential numbers and timestamps

**Configuration:**

- `INPUT_DIR`: Source directory for videos
- `OUTPUT_DIR`: Directory for extracted frames
- `MIN_FRAMES`: Minimum frames to extract per video
- `THRESHOLD`: FFmpeg scene detection threshold

### 2. crop_videos.py

Detects and removes black borders from videos using multiple methods.

**Features:**

- Uses three different methods to detect black borders:
  1. FFmpeg's cropdetect filter
  2. Median-based detection
  3. Gradient-based detection
- Only crops if significant borders are detected
- Preserves audio stream

**Configuration:**

- `INPUT_DIR`: Source directory for videos
- `OUTPUT_DIR`: Directory for cropped videos
- `SAMPLES`: Number of frames to sample
- `MIN_CROP_RATIO`: Minimum ratio of width/height to remove

### 3. rmv_blank_frames.py

Filters out blank (uniform color) frames from extracted frames.

**Features:**

- Recursively processes directories of frames
- Detects and removes frames that are uniform in color
- Maintains original directory structure
- Preserves non-blank frames

**Configuration:**

- `INPUT_ROOT`: Source directory containing frame folders
- `OUTPUT_ROOT`: Directory for filtered frames

## Requirements

- FFmpeg installed on the system
- Python 3.x
- Required Python packages:
  - OpenCV (cv2)
  - NumPy

## Usage

1. First, crop videos if needed:

```bash
python crop_videos.py
```

2. Extract frames from videos:

```bash
python extract_frames.py
```

3. Remove any blank frames:

```bash
python rmv_blank_frames.py
```

## Expected Output

- Cropped videos in the configured output directory
- Extracted frames named with sequential numbers and timestamps
- Filtered frames with blank frames removed

## Notes

- These tests are part of the VideoFramesSceneExtractor lambda function test suite
- Make sure FFmpeg is properly configured before running the tests
- The scripts can be run in sequence to process videos from raw input to final frame extraction
