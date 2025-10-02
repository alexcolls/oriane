#!/usr/bin/env python3

"""
Script to extract the most significant frames (one per detected scene) from all MP4 videos in a "videos" folder.
Uses PySceneDetect for scene detection and OpenCV for frame extraction.
Outputs images for each video under an "output/simple/<video_name>" directory, named 0.jpg, 1.jpg, ...
"""
import os
import cv2
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector

MIN_FRAMES = 4 # Minimum number of frames to extract per video
THRESHOLD = 8.0 # PySceneContentDetector threshold

def extract_key_frames(video_path, output_dir):
    # Prepare output directory for this video
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    video_output_dir = os.path.join(output_dir, video_name)
    os.makedirs(video_output_dir, exist_ok=True)
    
    # Open video and set up scene manager
    video_stream = open_video(video_path)
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=THRESHOLD))
    
    # Perform scene detection
    scene_manager.detect_scenes(video_stream)
    scene_list = scene_manager.get_scene_list()
    
    # Open video with OpenCV for frame extraction
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Get scene-detected frames
    scene_frame_indices = []
    for start_time, end_time in scene_list:
        start_frame = start_time.get_frames()
        end_frame = end_time.get_frames()
        scene_frame_indices.append((start_frame + end_frame) // 2)
    
    # If we have fewer frames than MIN_FRAMES, add evenly spaced frames
    if len(scene_frame_indices) < MIN_FRAMES:
        # Calculate evenly spaced frame indices
        step = total_frames // (MIN_FRAMES + 1)  # +1 to avoid including the last frame twice
        additional_frames = [i * step for i in range(1, MIN_FRAMES + 1)]
        
        # Combine scene frames with additional frames, maintaining order
        all_frames = sorted(set(scene_frame_indices + additional_frames))
        
        # If we still have fewer frames than MIN_FRAMES (e.g., no scenes detected),
        # take exactly MIN_FRAMES evenly spaced frames
        if len(all_frames) < MIN_FRAMES:
            all_frames = [i * (total_frames // (MIN_FRAMES + 1)) for i in range(1, MIN_FRAMES + 1)]
    else:
        all_frames = scene_frame_indices
    
    # Extract and save frames
    for idx, frame_no in enumerate(all_frames):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
        ret, frame = cap.read()
        if not ret:
            print(f"Warning: Could not read frame {frame_no} from {video_path}")
            continue
        cv2.imwrite(os.path.join(video_output_dir, f"{idx}.jpg"), frame)
    
    # Release resources
    cap.release()
    print(f"Extracted {len(all_frames)} frames from {video_path}")


def main():
    input_dir  = '../videos'
    output_dir = 'output/custom'
    os.makedirs(output_dir, exist_ok=True)
    for fname in os.listdir(input_dir):
        if not fname.lower().endswith('.mp4'):
            continue
        path = os.path.join(input_dir, fname)
        print(f"Processing {path}...")
        extract_key_frames(path, output_dir)
    print("Done extracting key frames.")


if __name__ == '__main__':
    main()
