# Video Processing Pipeline

A high-performance video processing pipeline that performs smart GPU-accelerated border cropping and scene frame extraction. This tool is designed to efficiently process video files by removing black borders and extracting meaningful frames from scenes.

## Features

- **Phase 1 - Smart GPU Border Crop**

  - GPU-accelerated video processing using NVIDIA CUDA
  - Intelligent border detection using multiple methods:
    - FFmpeg cropdetect
    - Gradient-based fallback detection
  - Parallel processing support for multiple videos
  - Hardware-accelerated encoding using NVENC

- **Phase 2 - Scene Frame Extraction**
  - Automatic scene change detection
  - Smart frame selection based on content
  - Automatic cropping of black borders in extracted frames
  - Fallback mechanism for videos with few scene changes
  - Timestamp-based frame naming

## Requirements

### System Requirements

- NVIDIA GPU with CUDA support
- FFmpeg with CUDA support
- Python 3.6 or higher (3.10 or 3.11 is recommended)

### Python Dependencies

- numpy >= 1.21.0
- opencv-python >= 4.5.0

### FFmpeg Requirements

- FFmpeg with CUDA support
- FFprobe

## Installation

1. Ensure you have FFmpeg with CUDA support installed:

   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install ffmpeg
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Directory Structure

```
.
├── src/
│   └── py/
│       └── main.py
├── videos/          # Input videos directory
├── tmp/
│   └── cropped/    # Temporary cropped videos
└── output/         # Extracted frames output
```

## Usage

1. Place your input videos in the `videos` directory
2. Run the pipeline:
   ```bash
   python src/py/main.py
   ```

The script will:

1. Process all videos in the input directory
2. Create cropped versions in the temporary directory
3. Extract meaningful frames to the output directory

## Configuration

The script includes several configurable parameters in `main.py`:

### Phase 1 (Cropping)

- `SAMPLE_FPS`: Frame sampling rate for analysis (default: 0.1)
- `MAX_WORKERS`: Number of parallel GPU workers (default: 3)
- `TOLERANCE`: Border detection tolerance (default: 5)
- `EDGE_THRESH`: Edge detection threshold (default: 10)
- `MIN_CROP_RATIO`: Minimum crop ratio (default: 0.10)
- `DOWNSCALE`: Downscaling factor for analysis (default: 0.5)

### Phase 2 (Frame Extraction)

- `MIN_FRAMES`: Minimum frames to extract (default: 4)
- `SCENE_THRESH`: Scene change threshold (default: 0.12)

### Housekeeping

- `REMOVE_TMP`: Whether to delete temporary cropped videos (default: False)

## Output

The extracted frames are saved in the `output` directory, organized in subdirectories named after the source videos. Each frame is named with its sequence number and timestamp:

```
output/
└── video_name/
    ├── 1_0.00.png
    ├── 2_10.50.png
    └── ...
```

## Notes

- The script requires NVIDIA GPU with CUDA support for optimal performance
- Supported input formats: MP4, MKV, MOV, AVI, WebM
- Output frames are saved in PNG format
- Temporary files can be automatically cleaned up by setting `REMOVE_TMP = True`

## Troubleshooting

1. **CUDA/GPU Issues**

   - Ensure NVIDIA drivers are up to date
   - Verify CUDA support in FFmpeg: `ffmpeg -hide_banner -filters | grep cuda`

2. **Performance Issues**

   - Adjust `MAX_WORKERS` based on your GPU memory
   - Modify `SAMPLE_FPS` for faster/slower processing

3. **Quality Issues**
   - Adjust `SCENE_THRESH` for more/fewer scene changes
   - Modify `MIN_FRAMES` to ensure sufficient frame extraction
