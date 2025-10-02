#include <iostream>
#include <string>
#include <vector>
#include <filesystem> // C++17 for path operations
#include <stdexcept>
#include <cstdio>     // For popen, pclose, fgets
#include <memory>     // For std::unique_ptr
#include <array>
#include <algorithm>
#include <regex>
#include <fstream>
#include <sstream>
#include <iomanip>    // For std::fixed, std::setprecision
#include <thread>     // For std::thread
#include <future>     // For std::async, std::future

// OpenCV headers
#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <opencv2/highgui.hpp> // For imread, imwrite, VideoCapture
#include <opencv2/videoio.hpp> // For VideoCapture constants

// Namespace alias for convenience
namespace fs = std::filesystem;

// --- Global Config ---
const fs::path INPUT_DIR = "../videos";
const fs::path CROPPED_DIR = "../tmp";
const fs::path FRAMES_DIR = "../output";

// Speed / quality knobs
const double SAMPLE_FPS = 0.1;
const int MAX_WORKERS = 3; // For parallel processing

// Crop-detect
const int TOLERANCE = 5;        // For detect_image_crop (Phase 2)
const int EDGE_THRESH = 10;     // For detect_gradient
const double MIN_CROP_RATIO = 0.10;
const double DOWNSCALE = 0.5;
const int FFMPEG_PROBES = 3;
const int PROBE_CLIP_SECS = 2;
const int SAFE_MARGIN_PX = 4;

// Scene-frame extract
const int MIN_FRAMES = 4;
const double SCENE_THRESH = 0.12;

// Housekeeping
const bool REMOVE_TMP = false;

// FFmpeg/FFprobe paths (assuming they are in PATH)
const std::string FFMPEG = "ffmpeg";
const std::string FFPROBE = "ffprobe";

// --- Tiny Helpers ---

// Struct to hold crop rectangle
struct CropRect {
    int x, y, w, h;
    bool valid = false;
};

// Function to execute a command and get its output (stdout)
std::string execute_command(const std::string& cmd, bool capture_stderr = false) {
    std::array<char, 128> buffer;
    std::string result;
    std::string full_cmd = cmd;
    if (capture_stderr) {
        full_cmd += " 2>&1"; // Redirect stderr to stdout
    }

    // Use popen to run the command and capture its output
    // Note: popen is platform-dependent to some extent (POSIX)
    // For Windows, _popen might be needed or a more robust solution like CreateProcess.
    std::unique_ptr<FILE, decltype(&pclose)> pipe(popen(full_cmd.c_str(), "r"), pclose);
    if (!pipe) {
        throw std::runtime_error("popen() failed for command: " + cmd);
    }
    while (fgets(buffer.data(), buffer.size(), pipe.get()) != nullptr) {
        result += buffer.data();
    }
    return result;
}

// Helper to get a value from ffprobe
std::string ffprobe_val(const std::string& src_path, const std::string& key) {
    std::string cmd = FFPROBE + " -v quiet -select_streams v:0 -show_entries stream=" + key + " -of csv=p=0 \"" + src_path + "\"";
    std::string output = execute_command(cmd);
    // Trim whitespace (Python's strip().lower())
    output.erase(0, output.find_first_not_of(" \n\r\t"));
    output.erase(output.find_last_not_of(" \n\r\t") + 1);
    std::transform(output.begin(), output.end(), output.begin(), ::tolower);
    return output;
}

// Helper to check if ffmpeg has a specific filter
bool ff_has_filter(const std::string& filter_name) {
    try {
        std::string cmd = FFMPEG + " -hide_banner -filters";
        std::string output = execute_command(cmd);
        return output.find(filter_name) != std::string::npos;
    } catch (const std::exception& e) {
        std::cerr << "Error checking for filter " << filter_name << ": " << e.what() << std::endl;
        return false;
    }
}

bool HAS_CROP_CUDA = ff_has_filter("crop_cuda");

// Helper to make an integer even (round up if odd)
int make_even(int x) {
    return (x % 2 == 0) ? x : x + 1;
}

// Decoder map (similar to Python's DECODER dictionary)
std::map<std::string, std::string> DECODER_MAP = {
    {"h264", "h264_cuvid"}, {"hevc", "hevc_cuvid"}, {"vp9", "vp9_cuvid"},
    {"av1", "av1_cuvid"}, {"mpeg2video", "mpeg2_cuvid"}
};

// --- Sampling Iterator (Conceptual C++ Version) ---
// This is complex because it involves continuously reading from ffmpeg's stdout pipe.
// For simplicity, this example won't fully implement the frame-by-frame iterator
// but will outline the approach. A more robust solution might use a library
// or platform-specific pipe handling.
// The Python version reads raw RGB24 data.

// --- FFmpeg CropDetect Union (Phase 1 Detector) ---
CropRect detect_crop_ffmpeg(const std::string& src_path) {
    std::string duration_str = ffprobe_val(src_path, "duration");
    double duration = 0.0;
    if (!duration_str.empty()) {
        try {
            duration = std::stod(duration_str);
        } catch (const std::exception& e) {
            std::cerr << "Warning: Could not parse duration: " << duration_str << std::endl;
            duration = 0.0;
        }
    }
    if (duration == 0) return {0,0,0,0,false};

    std::vector<CropRect> rects;
    for (int k = 0; k < FFMPEG_PROBES; ++k) {
        double ts = duration * (k + 1.0) / (FFMPEG_PROBES + 1.0);
        std::stringstream cmd_ss;
        cmd_ss << FFMPEG << " -hide_banner -loglevel error -ss " << std::fixed << std::setprecision(3) << ts
               << " -t " << PROBE_CLIP_SECS << " -hwaccel cuda -i \"" << src_path << "\""
               << " -vf cropdetect=24:16:0 -an -f null -";

        // Capture stderr because cropdetect logs there
        std::string output = execute_command(cmd_ss.str(), true);

        std::regex crop_regex("crop=([0-9]+):([0-9]+):([0-9]+):([0-9]+)");
        std::smatch match;
        std::string last_match_str;

        // Find all matches and use the last one
        auto it = std::sregex_iterator(output.begin(), output.end(), crop_regex);
        auto end = std::sregex_iterator();
        if (it != end) {
            std::smatch last_smatch;
            while(it != end) {
                last_smatch = *it;
                ++it;
            }
            if (last_smatch.size() == 5) {
                rects.push_back({
                    std::stoi(last_smatch[3].str()), // x
                    std::stoi(last_smatch[4].str()), // y
                    std::stoi(last_smatch[1].str()), // w
                    std::stoi(last_smatch[2].str())  // h
                });
                rects.back().valid = true;
            }
        }
    }

    if (rects.empty()) return {0,0,0,0,false};

    int min_x = rects[0].x, min_y = rects[0].y;
    int max_x_plus_w = rects[0].x + rects[0].w;
    int max_y_plus_h = rects[0].y + rects[0].h;

    for (size_t i = 1; i < rects.size(); ++i) {
        min_x = std::min(min_x, rects[i].x);
        min_y = std::min(min_y, rects[i].y);
        max_x_plus_w = std::max(max_x_plus_w, rects[i].x + rects[i].w);
        max_y_plus_h = std::max(max_y_plus_h, rects[i].y + rects[i].h);
    }

    int final_x = std::max(0, min_x - SAFE_MARGIN_PX);
    int final_y = std::max(0, min_y - SAFE_MARGIN_PX);
    int final_w = max_x_plus_w - final_x + SAFE_MARGIN_PX; // Recalculate width based on overall extent
    int final_h = max_y_plus_h - final_y + SAFE_MARGIN_PX; // Recalculate height

    // Correct width and height based on the original definition: x1-x0, y1-y0
    final_w = (max_x_plus_w + SAFE_MARGIN_PX) - (std::max(0, min_x - SAFE_MARGIN_PX));
    final_h = (max_y_plus_h + SAFE_MARGIN_PX) - (std::max(0, min_y - SAFE_MARGIN_PX));


    return {final_x, final_y, final_w, final_h, true};
}


// --- Gradient Fallback (using OpenCV) ---
CropRect detect_gradient(const std::string& src_path, int ow, int oh) {
    cv::Mat heat_map;
    bool heat_map_initialized = false;

    // Simplified frame iteration: Open video, grab some frames
    // This is a placeholder for the more complex iter_sampled_frames
    cv::VideoCapture cap(src_path);
    if (!cap.isOpened()) {
        std::cerr << "Error: Cannot open video file for gradient detection: " << src_path << std::endl;
        return {0,0,0,0,false};
    }

    double video_fps = cap.get(cv::CAP_PROP_FPS);
    if (video_fps == 0) video_fps = 25.0; // Default FPS if not available
    int frame_skip = static_cast<int>(video_fps / SAMPLE_FPS);
    if (frame_skip < 1) frame_skip = 1;

    cv::Mat frame;
    int frame_count = 0;
    int sampled_frames_count = 0;

    while (cap.read(frame)) {
        if (frame_count % frame_skip == 0) {
            cv::Mat small_frame;
            cv::resize(frame, small_frame, cv::Size(), DOWNSCALE, DOWNSCALE, cv::INTER_LINEAR);
            cv::cvtColor(small_frame, small_frame, cv::COLOR_BGR2RGB); // Assuming ffmpeg rawvideo was RGB

            cv::Mat gray, sx, sy, mag;
            cv::cvtColor(small_frame, gray, cv::COLOR_RGB2GRAY);
            cv::Sobel(gray, sx, CV_32F, 1, 0, 3);
            cv::Sobel(gray, sy, CV_32F, 0, 1, 3);
            cv::magnitude(sx, sy, mag);

            if (!heat_map_initialized) {
                heat_map = mag.clone();
                heat_map_initialized = true;
            } else {
                cv::add(heat_map, mag, heat_map);
            }
            sampled_frames_count++;
        }
        frame_count++;
        if (sampled_frames_count > 30 && SAMPLE_FPS < 1) break; // Limit frames for performance if sampling
         if (sampled_frames_count > 100 && SAMPLE_FPS >=1) break;
    }
    cap.release();

    if (!heat_map_initialized) return {0,0,0,0,false};

    cv::Mat norm_heat, mask;
    cv::normalize(heat_map, norm_heat, 0, 255, cv::NORM_MINMAX, CV_8U);
    cv::threshold(norm_heat, mask, EDGE_THRESH, 255, cv::THRESH_BINARY);

    cv::Mat kernel = cv::getStructuringElement(cv::MORPH_RECT, cv::Size(15, 15));
    cv::morphologyEx(mask, mask, cv::MORPH_CLOSE, kernel);

    std::vector<std::vector<cv::Point>> contours;
    cv::findContours(mask, contours, cv::RETR_EXTERNAL, cv::CHAIN_APPROX_SIMPLE);

    if (contours.empty()) return {0,0,0,0,false};

    // Find contour with max area
    double max_area = 0;
    cv::Rect best_rect;
    for (const auto& cnt : contours) {
        cv::Rect r = cv::boundingRect(cnt);
        if (r.area() > max_area) {
            max_area = r.area();
            best_rect = r;
        }
    }

    double s = 1.0 / DOWNSCALE;
    return {
        static_cast<int>(best_rect.x * s),
        static_cast<int>(best_rect.y * s),
        static_cast<int>(best_rect.width * s),
        static_cast<int>(best_rect.height * s),
        true
    };
}

// Good-enough check for a crop rectangle
bool is_good_crop(const CropRect& rect, int ow, int oh) {
    if (!rect.valid || rect.w <= 0 || rect.h <= 0) return false;
    bool significant_crop = (rect.w < ow * (1.0 - MIN_CROP_RATIO)) || (rect.h < oh * (1.0 - MIN_CROP_RATIO));
    bool sensible_size = (rect.w > 0.05 * ow && rect.h > 0.05 * oh);
    return significant_crop && sensible_size;
}

// --- GPU Crop + Encode ---
void crop_gpu(const std::string& src_path, const std::string& dst_path, const CropRect& rect, int ow, int oh) {
    int crop_w = make_even(rect.w);
    int crop_h = make_even(rect.h);

    std::string codec_name = ffprobe_val(src_path, "codec_name");
    std::string cuvid_decoder;
    if (DECODER_MAP.count(codec_name)) {
        cuvid_decoder = DECODER_MAP[codec_name];
    }

    std::stringstream cmd_ss;
    cmd_ss << FFMPEG << " -hide_banner -loglevel error ";

    // Input options
    if (HAS_CROP_CUDA) {
        if (!cuvid_decoder.empty()) {
            cmd_ss << "-c:v " << cuvid_decoder << " -hwaccel_device 0 -hwaccel_output_format cuda ";
        } else {
            cmd_ss << "-hwaccel cuda -hwaccel_device 0 -hwaccel_output_format cuda ";
        }
    } else if (!cuvid_decoder.empty()) {
         cmd_ss << "-c:v " << cuvid_decoder << " -hwaccel_device 0 ";
         int top = rect.y;
         int bottom = oh - (rect.y + rect.h);
         int left = rect.x;
         int right = ow - (rect.x + rect.w);
         cmd_ss << "-crop " << top << "x" << bottom << "x" << left << "x" << right << " ";
    } else {
        std::cerr << "Warning: No direct GPU crop path available for " << src_path << ". Falling back to CPU crop or ffmpeg's default." << std::endl;
        // Fallback: let ffmpeg handle it, might be slower or use CPU crop
    }

    cmd_ss << "-i \"" << src_path << "\" ";

    // Video filter options
    if (HAS_CROP_CUDA) {
        cmd_ss << "-vf \"crop_cuda=w=" << crop_w << ":h=" << crop_h << ":x=" << rect.x << ":y=" << rect.y
               << ",setsar=1:1,format=nv12\" ";
    } else if (!cuvid_decoder.empty()) { // If using cuvid but not crop_cuda (older ffmpeg)
        cmd_ss << "-vf \"setsar=1:1,format=nv12\" "; // SAR and format might be needed after cuvid -crop
    } else { // General case, possibly CPU cropping
         cmd_ss << "-vf \"crop=" << crop_w << ":" << crop_h << ":" << rect.x << ":" << rect.y
               << ",setsar=1:1,format=nv12\" "; // format=yuv420p is more common for h264
    }


    // Output options
    cmd_ss << "-c:v h264_nvenc -preset p5 -tune hq -cq 23 -c:a copy -movflags +faststart -y \"" << dst_path << "\"";

    std::cout << "Executing crop: " << cmd_ss.str() << std::endl;
    int ret = system(cmd_ss.str().c_str()); // Using system for simplicity. Robust apps use CreateProcess/fork+exec.
    if (ret != 0) {
        throw std::runtime_error("ffmpeg crop_gpu command failed for " + src_path);
    }
}


// --- Worker for Phase 1 ---
std::string handle_video_phase1(const fs::path& src_path_fs) {
    std::string src_path = src_path_fs.string();
    std::cout << "Processing (Phase 1): " << src_path << std::endl;

    std::string width_str = ffprobe_val(src_path, "width");
    std::string height_str = ffprobe_val(src_path, "height");
    int ow = 0, oh = 0;
    if (!width_str.empty() && !height_str.empty()) {
        try {
            ow = std::stoi(width_str);
            oh = std::stoi(height_str);
        } catch(const std::exception& e) {
            std::cerr << "Error parsing dimensions for " << src_path << ": " << e.what() << std::endl;
            return "error_dimensions";
        }
    } else {
         std::cerr << "Error: Could not get dimensions for " << src_path << std::endl;
         return "error_dimensions";
    }


    fs::path dst_path_fs = CROPPED_DIR / src_path_fs.filename();
    std::string dst_path = dst_path_fs.string();

    CropRect rect = detect_crop_ffmpeg(src_path);
    std::string mode = "ffmpeg";

    if (!is_good_crop(rect, ow, oh)) {
        std::cout << "  FFmpeg crop not good or not found for " << src_path_fs.filename() << ". Trying gradient detection." << std::endl;
        CropRect alt_rect = detect_gradient(src_path, ow, oh);
        if (is_good_crop(alt_rect, ow, oh)) {
            rect = alt_rect;
            mode = "gradient";
            std::cout << "  Gradient detection successful for " << src_path_fs.filename() << std::endl;
        } else {
             std::cout << "  Gradient detection also not good for " << src_path_fs.filename() << std::endl;
        }
    }

    if (rect.valid && is_good_crop(rect, ow, oh)) { // Ensure rect is valid before using
        try {
            std::cout << "  Cropping " << src_path_fs.filename() << " using " << mode
                      << " to x:" << rect.x << " y:" << rect.y << " w:" << rect.w << " h:" << rect.h << std::endl;
            crop_gpu(src_path, dst_path, rect, ow, oh);
            return "crop[" + mode + "]";
        } catch (const std::exception& e) {
            std::cerr << "  Error cropping " << src_path_fs.filename() << ": " << e.what() << std::endl;
            std::cerr << "  Copying instead." << std::endl;
            fs::copy_file(src_path_fs, dst_path_fs, fs::copy_options::overwrite_existing);
            return "copy_after_error";
        }
    } else {
        std::cout << "  No good crop found for " << src_path_fs.filename() << ". Copying original." << std::endl;
        fs::copy_file(src_path_fs, dst_path_fs, fs::copy_options::overwrite_existing);
        return "copy";
    }
}

// --- Phase 2: Frame Extraction Helpers ---

// Detect image crop (borders of solid color)
CropRect detect_image_crop_cv(const cv::Mat& img, int tol = TOLERANCE) {
    if (img.empty()) return {0,0,0,0,false};
    int h = img.rows;
    int w = img.cols;

    auto is_blank_line = [&](const cv::Mat& line_roi, bool is_row) {
        if (line_roi.empty() || line_roi.total() == 0) return true;

        cv::Mat medians;
        // Calculate median along the appropriate axis
        // For a row (line_roi is 1xW or Hx1), reduce to 1x1 median per channel
        // OpenCV's reduce doesn't directly compute median. We need to do it manually or approximate.
        // Python version uses np.median(line, 0)
        // A simple approximation: check if most pixels are very similar to the first pixel.
        // Or, for simplicity, check against a fixed color like black or white if that's common.
        // The Python version is more robust. This is a simplified version.

        // Let's try a more direct translation of the Python logic:
        // For each pixel in the line, compare to median of that line.
        // This is computationally intensive if done per pixel naively.
        // Python: med=np.median(line,0); return np.all(np.abs(line.astype(int)-med.astype(int)).sum(1)<=tol)

        // Simplified: Check if average intensity is very low or very high (near black/white)
        // Or if variance is very low.
        // For this example, let's use a simplified version of the Python logic
        // by checking if all pixels are close to the mean of the line.
        cv::Scalar mean_val = cv::mean(line_roi);
        for (int i = 0; i < (is_row ? line_roi.cols : line_roi.rows); ++i) {
            cv::Vec3b p = is_row ? line_roi.at<cv::Vec3b>(0, i) : line_roi.at<cv::Vec3b>(i, 0);
            int diff_sum = std::abs(p[0] - static_cast<int>(mean_val[0])) +
                           std::abs(p[1] - static_cast<int>(mean_val[1])) +
                           std::abs(p[2] - static_cast<int>(mean_val[2]));
            if (diff_sum > tol * 3) { // tol for each channel
                return false;
            }
        }
        return true;
    };

    int x0 = w, x1 = 0, y0 = h, y1 = 0;

    for (int x = 0; x < w; ++x) if (!is_blank_line(img.col(x), false)) { x0 = x; break; }
    for (int x = w - 1; x >= 0; --x) if (!is_blank_line(img.col(x), false)) { x1 = x; break; }
    for (int y = 0; y < h; ++y) if (!is_blank_line(img.row(y), true)) { y0 = y; break; }
    for (int y = h - 1; y >= 0; --y) if (!is_blank_line(img.row(y), true)) { y1 = y; break; }

    if (x0 >= x1 || y0 >= y1) return {0,0,0,0,false};
    return {x0, y0, x1 - x0 + 1, y1 - y0 + 1, true};
}

// Extract scene keyframes using ffmpeg
std::vector<fs::path> ffmpeg_scene_jpgs(const std::string& video_path_str, const fs::path& tmp_dir, double threshold) {
    if (!fs::exists(tmp_dir)) {
        fs::create_directories(tmp_dir);
    }
    fs::path out_pattern = tmp_dir / "%d.png"; // ffmpeg uses %d for frame number

    std::stringstream cmd_ss;
    cmd_ss << FFMPEG << " -hide_banner -loglevel error -i \"" << video_path_str << "\""
           << " -vf \"select='gt(scene\\," << std::fixed << std::setprecision(3) << threshold << ")'\""
           << " -vsync vfr -frame_pts 1 -q:v 2 \"" << out_pattern.string() << "\"";

    std::cout << "  Executing scene detection: " << cmd_ss.str() << std::endl;
    int ret = system(cmd_ss.str().c_str());
    if (ret != 0) {
        std::cerr << "  Warning: ffmpeg scene detection command failed for " << video_path_str << std::endl;
        return {};
    }

    std::vector<fs::path> jpgs;
    for (const auto& entry : fs::directory_iterator(tmp_dir)) {
        if (entry.is_regular_file() && entry.path().extension() == ".png") {
            // Ensure the stem is a number
            try {
                std::stoi(entry.path().stem().string());
                jpgs.push_back(entry.path());
            } catch (const std::invalid_argument& ia) {
                // Not a frame file like "1.png", skip
            }
        }
    }
    // Sort by frame number (integer value of stem)
    std::sort(jpgs.begin(), jpgs.end(), [](const fs::path& a, const fs::path& b){
        return std::stoi(a.stem().string()) < std::stoi(b.stem().string());
    });
    return jpgs;
}

// Main frame extraction logic for a single video (Phase 2)
void extract_frames_for_video(const fs::path& video_file) {
    std::string base_stem = video_file.stem().string();
    fs::path out_dir = FRAMES_DIR / base_stem;

    std::cout << "  Extracting frames for " << video_file.filename().string() << " -> " << out_dir.string() << std::endl;
    if (!fs::exists(out_dir)) {
        fs::create_directories(out_dir);
    }

    // Temporary directory for ffmpeg's initial scene cuts (will be cleaned up)
    fs::path temp_scene_cut_dir = out_dir / "scene_cuts_temp";

    std::vector<fs::path> scene_pngs = ffmpeg_scene_jpgs(video_file.string(), temp_scene_cut_dir, SCENE_THRESH);

    cv::VideoCapture cap_fps(video_file.string());
    double fps = cap_fps.get(cv::CAP_PROP_FPS);
    if (fps == 0) fps = 25.0; // Default
    cap_fps.release();

    int final_frame_idx = 1;
    for (const fs::path& png_path : scene_pngs) {
        cv::Mat img = cv::imread(png_path.string());
        if (img.empty()) {
            fs::remove(png_path);
            continue;
        }

        CropRect crop_info = detect_image_crop_cv(img);
        cv::Mat final_img = img;
        if (crop_info.valid) {
            final_img = img(cv::Rect(crop_info.x, crop_info.y, crop_info.w, crop_info.h));
        }

        cv::Mat gray;
        cv::cvtColor(final_img, gray, cv::COLOR_BGR2GRAY);
        // Check if frame is all one color (blank)
        double min_val, max_val;
        cv::minMaxLoc(gray, &min_val, &max_val);
        if (min_val == max_val) { // All pixels are the same
            fs::remove(png_path);
            continue;
        }

        // Frame number from filename (e.g., "123.png")
        int frame_no = 0;
        try {
             frame_no = std::stoi(png_path.stem().string());
        } catch (const std::exception& e) {
            std::cerr << "Could not parse frame number from: " << png_path.stem().string() << std::endl;
            fs::remove(png_path);
            continue;
        }

        double timestamp = static_cast<double>(frame_no) / fps; // frame_pts was used, so frame_no is effectively timestamp if original fps=1
                                                                // If ffmpeg -frame_pts 1 writes actual frame number, then this is correct.
                                                                // Python script uses frame_no / fps. Let's stick to that.

        std::stringstream new_name_ss;
        new_name_ss << final_frame_idx << "_" << std::fixed << std::setprecision(2) << timestamp << ".png";
        fs::path final_frame_path = out_dir / new_name_ss.str();
        cv::imwrite(final_frame_path.string(), final_img);

        fs::remove(png_path); // Clean up temp png
        final_frame_idx++;
    }
     if (fs::exists(temp_scene_cut_dir)) { // Clean up temp directory for scene cuts
        fs::remove_all(temp_scene_cut_dir);
    }


    // Fallback if not enough frames
    if (final_frame_idx <= MIN_FRAMES) {
        std::cout << "    Fallback: Grabbing more frames for " << video_file.filename() << "..." << std::endl;
        cv::VideoCapture cap(video_file.string());
        if (!cap.isOpened()) {
            std::cerr << "    Error: Cannot open video for fallback: " << video_file.string() << std::endl;
            return;
        }
        long total_frames = static_cast<long>(cap.get(cv::CAP_PROP_FRAME_COUNT));
        long step = std::max(1L, total_frames / (MIN_FRAMES + 1));

        // Start fallback frames from where scene detection left off, or from 1 if no scenes found
        int current_fallback_count = final_frame_idx;

        for (int i = 0; (current_fallback_count <= MIN_FRAMES) && i < (MIN_FRAMES*2); ++i) { // Limit iterations
            long pos = (current_fallback_count -1) * step; // Use current_fallback_count to determine position
            if (pos >= total_frames && total_frames > 0) break;

            cap.set(cv::CAP_PROP_POS_FRAMES, static_cast<double>(pos));
            cv::Mat frame;
            if (!cap.read(frame) || frame.empty()) break;

            CropRect crop_info = detect_image_crop_cv(frame);
            cv::Mat final_frame = frame;
             if (crop_info.valid) {
                final_frame = frame(cv::Rect(crop_info.x, crop_info.y, crop_info.w, crop_info.h));
            } else { // If no crop, use full frame
                // No explicit else needed, final_frame is already 'frame'
            }


            cv::Mat gray;
            cv::cvtColor(final_frame, gray, cv::COLOR_BGR2GRAY);
            double min_val, max_val;
            cv::minMaxLoc(gray, &min_val, &max_val);
            if (min_val == max_val) continue; // Skip blank frame

            double ts = static_cast<double>(pos) / fps;
            std::stringstream out_name_ss;
            out_name_ss << current_fallback_count << "_" << std::fixed << std::setprecision(2) << ts << ".png";
            cv::imwrite((out_dir / out_name_ss.str()).string(), final_frame);
            current_fallback_count++;
        }
        cap.release();
        final_frame_idx = current_fallback_count; // Update final_frame_idx with frames added by fallback
    }
    std::cout << "    Kept " << (final_frame_idx - 1) << " frames for " << video_file.filename() << std::endl;
}


// --- Main Orchestrator ---
void phase1_crop() {
    std::vector<fs::path> vids;
    std::vector<std::string> extensions = {".mp4", ".mkv", ".mov", ".avi", ".webm"};
    if (!fs::exists(INPUT_DIR) || !fs::is_directory(INPUT_DIR)) {
        std::cerr << "Input directory " << INPUT_DIR << " does not exist or is not a directory." << std::endl;
        return;
    }

    for (const auto& entry : fs::directory_iterator(INPUT_DIR)) {
        if (entry.is_regular_file()) {
            std::string ext = entry.path().extension().string();
            std::transform(ext.begin(), ext.end(), ext.begin(), ::tolower);
            if (std::find(extensions.begin(), extensions.end(), ext) != extensions.end()) {
                vids.push_back(entry.path());
            }
        }
    }
    std::sort(vids.begin(), vids.end());

    if (vids.empty()) {
        std::cout << "No videos found in " << INPUT_DIR << "." << std::endl;
        return;
    }

    if (!fs::exists(CROPPED_DIR)) {
        fs::create_directories(CROPPED_DIR);
    }

    std::cout << "Cropping " << vids.size() << " videos with up to " << MAX_WORKERS << " workers..." << std::endl;
    auto start_time = std::chrono::high_resolution_clock::now();

    if (MAX_WORKERS <= 1) {
        for (const auto& v : vids) {
            try {
                handle_video_phase1(v);
            } catch (const std::exception& e) {
                std::cerr << "Error processing " << v.string() << ": " << e.what() << std::endl;
            }
        }
    } else {
        std::vector<std::future<std::string>> futures;
        for (const auto& v : vids) {
            if (futures.size() >= MAX_WORKERS) {
                // Wait for one to complete
                 bool one_completed = false;
                 while(!one_completed) {
                    for(size_t i=0; i < futures.size(); ++i) {
                        if (futures[i].wait_for(std::chrono::seconds(0)) == std::future_status::ready) {
                            try { futures[i].get(); } catch (const std::exception& e) { std::cerr << "Thread error: " << e.what() << std::endl; }
                            futures.erase(futures.begin() + i);
                            one_completed = true;
                            break;
                        }
                    }
                    if (!one_completed) std::this_thread::sleep_for(std::chrono::milliseconds(100)); // Don't busy-wait
                 }
            }
            futures.push_back(std::async(std::launch::async, handle_video_phase1, v));
        }
        // Wait for remaining tasks
        for (auto& fut : futures) {
            try { fut.get(); } catch (const std::exception& e) { std::cerr << "Thread error: " << e.what() << std::endl; }
        }
    }

    auto end_time = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> diff = end_time - start_time;
    std::cout << "Phase 1 (cropping) done in " << std::fixed << std::setprecision(1) << diff.count() << "s" << std::endl;
}

void phase2_extract() {
    std::vector<fs::path> cropped_videos;
     if (!fs::exists(CROPPED_DIR) || !fs::is_directory(CROPPED_DIR)) {
        std::cout << "Cropped directory " << CROPPED_DIR << " does not exist. Nothing to extract." << std::endl;
        return;
    }
    for (const auto& entry : fs::directory_iterator(CROPPED_DIR)) {
        if (entry.is_regular_file() && (entry.path().extension() == ".mp4")) { // Python script specifically looks for .mp4
            cropped_videos.push_back(entry.path());
        }
    }
    std::sort(cropped_videos.begin(), cropped_videos.end());


    if (cropped_videos.empty()) {
        std::cout << "No cropped videos found in " << CROPPED_DIR << " to extract from." << std::endl;
        return;
    }

    if (!fs::exists(FRAMES_DIR)) {
        fs::create_directories(FRAMES_DIR);
    }

    std::cout << "Extracting scene frames from " << cropped_videos.size() << " cropped videos..." << std::endl;
    auto start_time = std::chrono::high_resolution_clock::now();

    // Phase 2 can also be parallelized, but for simplicity, let's do it sequentially here.
    // The Python script does it sequentially.
    for (const auto& vid_path : cropped_videos) {
        try {
            extract_frames_for_video(vid_path);
        } catch (const std::exception& e) {
            std::cerr << "Error extracting frames from " << vid_path.string() << ": " << e.what() << std::endl;
        }
    }

    auto end_time = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> diff = end_time - start_time;
    std::cout << "Phase 2 (frame extraction) done in " << std::fixed << std::setprecision(1) << diff.count() << "s" << std::endl;


    if (REMOVE_TMP) {
        std::cout << "REMOVE_TMP = true. Deleting temporary cropped videos..." << std::endl;
        for (const auto& vid_path : cropped_videos) {
            try {
                fs::remove(vid_path);
            } catch (const fs::filesystem_error& e) {
                std::cerr << "Error deleting " << vid_path.string() << ": " << e.what() << std::endl;
            }
        }
        try {
            if (fs::is_empty(CROPPED_DIR)) { // Only remove if empty
                fs::remove(CROPPED_DIR);
            } else {
                std::cout << "Warning: " << CROPPED_DIR << " is not empty. Not removing." << std::endl;
            }
        } catch (const fs::filesystem_error& e) {
             std::cerr << "Error deleting directory " << CROPPED_DIR.string() << ": " << e.what() << std::endl;
        }
    }
}


int main() {
    // Check for ffmpeg/ffprobe (basic check)
    if (system((FFMPEG + " -version > nul 2>&1").c_str()) != 0 && system((FFMPEG + " -version > /dev/null 2>&1").c_str()) != 0) { // Windows and Linux check
        std::cerr << "ffmpeg not found in PATH. Please install ffmpeg." << std::endl;
        return 1;
    }
    if (system((FFPROBE + " -version > nul 2>&1").c_str()) != 0 && system((FFPROBE + " -version > /dev/null 2>&1").c_str()) != 0) {
        std::cerr << "ffprobe not found in PATH. Please install ffprobe." << std::endl;
        return 1;
    }

    HAS_CROP_CUDA = ff_has_filter("crop_cuda"); // Re-check, might be useful
    std::cout << "crop_cuda filter available: " << (HAS_CROP_CUDA ? "Yes" : "No") << std::endl;


    auto total_start_time = std::chrono::high_resolution_clock::now();

    try {
        phase1_crop();
        phase2_extract();
    } catch (const std::exception& e) {
        std::cerr << "An unhandled error occurred: " << e.what() << std::endl;
        return 1;
    }

    auto total_end_time = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> total_diff = total_end_time - total_start_time;
    std::cout << "Total time: " << std::fixed << std::setprecision(1) << total_diff.count() << "s" << std::endl;

    return 0;
}
