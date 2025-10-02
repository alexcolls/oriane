# VideoFramesSceneExtractor

A Python toolset for extracting key frames from videos based on scene detection. This repository contains two scripts:
- **simple.py**: Basic implementation for quick scene extraction
- **advanced.py**: Feature-rich implementation with configurable options and optimizations

## Overview

Both scripts analyze videos to detect scene changes and extract representative frames from each scene. They use [PySceneDetect](https://www.scenedetect.com/features/) for scene detection and OpenCV for frame extraction and processing.

## Requirements

- Python 3.6+
- OpenCV (`cv2`)
- PySceneDetect
- NumPy (for advanced.py)
- tqdm (for advanced.py progress bars)

Install dependencies with:

```
pip install opencv-python scenedetect numpy tqdm
```

## Directory Structure

```
VideoFramesSceneExtractor/
├── videos/                  # Place input MP4 videos here
├── output/
│   ├── simple/              # Output from simple.py
│   │   ├── video_name_1/    # One folder per video
│   │   │   ├── 0.jpg        # One image per scene
│   │   │   ├── 1.jpg
│   │   │   └── ...
│   │   └── ...
│   └── advanced/            # Output from advanced.py
│       └── ...
├── simple.py                # Basic implementation
└── advanced.py              # Advanced implementation
```

## Simple Implementation (simple.py)

### Features

- Straightforward implementation with minimal configuration
- Uses ContentDetector algorithm for scene detection
- Extracts the middle frame from each detected scene

### How It Works

1. Scans the `videos/` directory for MP4 files
2. For each video:
   - Creates an output directory at `output/simple/<video_name>/`
   - Performs scene detection using PySceneDetect's ContentDetector
   - For each detected scene, calculates the middle frame
   - Extracts and saves these frames as sequential JPG files (0.jpg, 1.jpg, etc.)

### Usage

```
python simple.py
```

## Advanced Implementation (advanced.py)

### Features

- Multiple scene detection algorithms (Content, Threshold, Histogram)
- Intelligent frame selection (picks the sharpest frame in each scene)
- Fallback mechanism if no scenes are detected
- Parallel processing for faster execution
- Progress bars for visual feedback
- Comprehensive logging
- Command-line configuration options

### How It Works

1. Parses command-line arguments for customization
2. Scans the `videos/` directory for MP4 files
3. For each video (processed in parallel):
   - Creates an output directory
   - Performs scene detection using the selected detector and parameters
   - For each scene, analyzes all frames to find the sharpest one using Laplacian variance
   - If no scenes are detected, falls back to extracting the video's middle frame
   - Saves extracted frames as sequential JPG files

### Frame Sharpness Analysis

The advanced script uses the variance of the Laplacian to determine frame sharpness. This is a common technique in computer vision for measuring focus quality. Higher variance indicates a sharper image.

### Command-Line Options

```
python advanced.py [options]

Options:
  --detector {content,threshold,histogram}
                        Which PySceneDetect detector to use (default: content)
  --threshold THRESHOLD
                        Sensitivity threshold (lower = more scenes) (default: 30.0)
  --min-scene-len MIN_SCENE_LEN
                        Minimum number of frames per scene (default: 1)
  --workers WORKERS     Number of parallel worker processes (default: CPU count)
  --output-dir OUTPUT_DIR
                        Base folder where per-video subfolders will be created (default: output)
```

### Usage Examples

Basic usage with defaults:
```
python advanced.py
```

Using histogram detector with custom threshold:
```
python advanced.py --detector histogram --threshold 20.0
```

Limiting CPU usage and specifying output directory:
```
python advanced.py --workers 2 --output-dir custom_frames
```

## Comparison

| Feature | simple.py | advanced.py |
|---------|-----------|-------------|
| Scene detection | Content detector only | Content, Threshold, or Histogram |
| Frame selection | Middle frame | Sharpest frame (using Laplacian) |
| Fallback mechanism | No | Yes (extracts mid-point if no scenes) |
| Parallel processing | No | Yes |
| Progress visualization | No | Yes (via tqdm) |
| Logging | Basic | Comprehensive |
| Configuration | Fixed | Command-line arguments |
| Processing speed | Slower | Faster with parallel workers |

## Running Test Configurations (tests.sh)

The repository includes a `tests.sh` script that demonstrates different detector configurations. This script runs the advanced implementation with various parameters to showcase different scene detection approaches.

```bash
# Run all test configurations
bash tests.sh
```

### Detector Types and Thresholds

#### --detector content
Uses the ContentDetector, which analyzes the content of frames to detect scene changes based on visual differences between consecutive frames. It's the most versatile detector, effective for most types of cuts and transitions in standard video content.

#### --threshold 25.0 (for ContentDetector)
Sets the threshold for content difference between frames. Lower values (like 25.0) make the detector more sensitive, catching subtle scene changes. Higher values would only detect more dramatic visual changes. For ContentDetector, this represents the level of content change required to trigger a scene cut.

#### --detector threshold
Uses the ThresholdDetector, which flags a cut whenever the count of pixels that change by more than a small amount between frames exceeds your threshold value. This can be more robust to gradual brightness shifts or camera noise than pure per-pixel averaging.

#### --threshold 10.0 (for ThresholdDetector)
Sets that pixel-count cutoff to 10.0. In practice, this means "if at least 10% of the pixels in the frame differ by your detector's internal per-pixel delta, call it a cut." (Adjusting this up/down makes the detector more/less sensitive to motion.)

#### --detector histogram
Uses the HistogramDetector, which compares color histograms between frames to detect changes. This detector is especially good at catching gradual transitions like fades, dissolves, and wipes that other detectors might miss.

#### --threshold 0.3 (for HistogramDetector)
Sets the threshold for histogram difference between frames. This low value (0.3) allows detection of subtle color distribution changes, making it ideal for catching gradual transitions. For HistogramDetector, the threshold represents the delta in color histogram required to identify a scene transition.

### General Parameters

#### --min-scene-len 30
Requires each detected scene to last at least 30 frames before it's accepted.

At 30 fps, that's 1 second.

Any candidate cut that would produce a scene shorter than 30 frames is discarded, merging it with its neighbors.

This filters out any jarring "flashes" or very rapid cuts under 1 second, so your extracted frames represent only the longer, more meaningful shots.

#### --workers 1
Runs everything single-threaded (one process). Useful if you want strictly ordered logs or avoid parallel I/O on a spinning disk.

Setting this higher (e.g., --workers 4) would process multiple videos simultaneously, utilizing more CPU cores for faster overall processing.

#### --output-dir [name]
Writes all per-video subfolders (and their 0.jpg, 1.jpg, etc.) under the folder named [name]/ instead of the default output/.

In the test script, each detector configuration uses its own named output directory (content/, threshold/, or histogram/), making it easy to compare results.

### Test Configurations

The test script runs three different configurations:

1. **Content detector** with high sensitivity (threshold=25.0) for detecting detailed visual changes
2. **Threshold detector** with medium sensitivity (threshold=10.0) for detecting significant pixel changes
3. **Histogram detector** with high sensitivity (threshold=0.3) for detecting gradual transitions

Each configuration uses the same minimum scene length (30 frames) and single-threaded processing to ensure comparable results.

## Technical Notes

- Both scripts require a `videos` directory in the same location as the script
- Output directory structure is automatically created
- For the advanced script, detector sensitivity can be tuned with the `--threshold` parameter (lower values create more scenes)
