#include <iostream>
#include <string>
#include <stdexcept> // For std::runtime_error, std::stoi exceptions
#include <vector>   // For std::vector (not strictly used but good include)
#include <sstream>  // For std::ostringstream
#include <cstdlib>  // For EXIT_FAILURE, EXIT_SUCCESS (though main returns int)

// FFmpeg headers
extern "C" {
#include <libavformat/avformat.h>
#include <libavcodec/avcodec.h>
#include <libavfilter/avfilter.h>
#include <libavfilter/buffersink.h>
#include <libavfilter/buffersrc.h>  // Added for av_buffersrc_set_hwframe_ctx
#include <libavutil/hwcontext.h>
#include <libavutil/hwcontext_cuda.h> // For AV_PIX_FMT_CUDA and AVHWFramesContext
#include <libavutil/pixfmt.h>
#include <libavutil/pixdesc.h>
#include <libavutil/opt.h>
#include <libavutil/imgutils.h> // For av_image_alloc (not directly used here but often useful)
}

// --- Configuration (can be overridden by command line args) ---
const char *default_output_filename_const = "output/simple_crop/cropped_video.mp4"; // Renamed to avoid conflict
int CROP_W_val = 640;
int CROP_H_val = 360;
int CROP_X_val = 100;
int CROP_Y_val = 50;
// --- End Configuration ---


// Helper function to convert AVERROR to string
static std::string av_error_to_string(int errnum) {
    char errbuf[AV_ERROR_MAX_STRING_SIZE];
    av_strerror(errnum, errbuf, AV_ERROR_MAX_STRING_SIZE);
    return std::string(errbuf);
}

// Global initialization for FFmpeg (call once)
static void initialize_ffmpeg() {
    // av_register_all(); // Deprecated in modern FFmpeg, not needed.
    // avfilter_register_all(); // Deprecated
    avformat_network_init(); // Still useful if dealing with network streams.
    std::cout << "FFmpeg initialized (including network and filter)." << std::endl;
}

// Callback to get HW pixel format for decoder
static enum AVPixelFormat get_hw_format(AVCodecContext *ctx, const enum AVPixelFormat *pix_fmts) {
    const enum AVPixelFormat *p;
    for (p = pix_fmts; *p != AV_PIX_FMT_NONE; p++) { // Iterate until AV_PIX_FMT_NONE
        if (*p == AV_PIX_FMT_CUDA) {
            std::cout << "get_hw_format: Found AV_PIX_FMT_CUDA in supported formats." << std::endl;
            return *p;
        }
    }
    std::cerr << "get_hw_format: Failed to find AV_PIX_FMT_CUDA. Check CUDA toolkit and FFmpeg build." << std::endl;
    return AV_PIX_FMT_NONE;
}

// Global FFmpeg contexts and references - carefully managed
AVFormatContext *output_format_ctx_global = nullptr;
AVCodecContext *encoder_ctx_global = nullptr;
AVFilterGraph *filter_graph_global = nullptr;
AVFilterContext *buffersrc_ctx_global = nullptr;
AVFilterContext *buffersink_ctx_global = nullptr;
AVBufferRef *hw_device_ctx_ref_global = nullptr; // Global CUDA device context

// In main.cpp, within the init_filters function

static int init_filters(AVCodecContext *dec_ctx_for_filter_props) {
    int ret = 0;
    const AVFilter *buffersrc_filter_ptr = avfilter_get_by_name("buffer");
    const AVFilter *buffersink_filter_ptr = avfilter_get_by_name("buffersink");
    AVFilterInOut *outputs = avfilter_inout_alloc();
    AVFilterInOut *inputs = avfilter_inout_alloc();
    enum AVPixelFormat sink_pix_fmts[] = {AV_PIX_FMT_CUDA, AV_PIX_FMT_NONE};
    AVBufferSrcParameters *src_par = nullptr; // Declare here, initialized to nullptr
    std::ostringstream src_args;        // moved up
    std::ostringstream filter_spec_ss;
    std::string filter_spec_str;

    filter_graph_global = avfilter_graph_alloc();
    if (!outputs || !inputs || !filter_graph_global) {
        std::cerr << "Failed to allocate filter graph, inputs, or outputs." << std::endl;
        ret = AVERROR(ENOMEM);
        goto end;
    }

    if (dec_ctx_for_filter_props->time_base.num == 0 || dec_ctx_for_filter_props->time_base.den == 0) {
        std::cerr << "Warning: Timebase for filter source is invalid in init_filters. Defaulting to 1/25." << std::endl;
        dec_ctx_for_filter_props->time_base = (AVRational){1, 25};
    }
    if (dec_ctx_for_filter_props->sample_aspect_ratio.num == 0 || dec_ctx_for_filter_props->sample_aspect_ratio.den == 0) {
        dec_ctx_for_filter_props->sample_aspect_ratio = (AVRational){1,1};
    }
    if (dec_ctx_for_filter_props->pix_fmt == AV_PIX_FMT_NONE) {
        std::cerr << "Error: dec_ctx_for_filter_props->pix_fmt is AV_PIX_FMT_NONE. Cannot proceed." << std::endl;
        ret = AVERROR(EINVAL);
        goto end;
    }

    // Build proper option string with pixel format included
    src_args << "video_size=" << dec_ctx_for_filter_props->width << 'x' << dec_ctx_for_filter_props->height
             << ":pix_fmt=" << av_get_pix_fmt_name(AV_PIX_FMT_CUDA)
             << ":time_base=" << dec_ctx_for_filter_props->time_base.num << '/' << dec_ctx_for_filter_props->time_base.den
             << ":pixel_aspect=" << dec_ctx_for_filter_props->sample_aspect_ratio.num << '/'
                                << dec_ctx_for_filter_props->sample_aspect_ratio.den;

    std::cout << "Buffer Source Args: " << src_args.str() << std::endl;

    ret = avfilter_graph_create_filter(&buffersrc_ctx_global,
                                     buffersrc_filter_ptr, "in",
                                     src_args.str().c_str(), // Now includes pix_fmt=cuda
                                     nullptr, filter_graph_global);
    if (ret < 0) {
        std::cerr << "Cannot create buffer source with complete args: " << av_error_to_string(ret) << std::endl;
        goto end;
    }

    src_par = av_buffersrc_parameters_alloc();
    if (!src_par) {
        std::cerr << "Failed to allocate buffer source parameters" << std::endl;
        ret = AVERROR(ENOMEM);
        goto end;
    }

    // No need to set src_par->format as it's already specified in the option string
    src_par->width            = dec_ctx_for_filter_props->width;
    src_par->height           = dec_ctx_for_filter_props->height;
    src_par->time_base        = dec_ctx_for_filter_props->time_base;
    src_par->sample_aspect_ratio = dec_ctx_for_filter_props->sample_aspect_ratio;
    src_par->hw_frames_ctx    = nullptr; // Initialize to NULL

    // Now declare pix_fmt_desc and perform logic that might jump to end
    {
        const AVPixFmtDescriptor *pix_fmt_desc = av_pix_fmt_desc_get(AV_PIX_FMT_CUDA);

        if (pix_fmt_desc && (pix_fmt_desc->flags & AV_PIX_FMT_FLAG_HWACCEL)) {
            if (dec_ctx_for_filter_props->hw_frames_ctx) {
                src_par->hw_frames_ctx = av_buffer_ref(dec_ctx_for_filter_props->hw_frames_ctx);
                if (!src_par->hw_frames_ctx) {
                    std::cerr << "Failed to reference hw_frames_ctx for AVBufferSrcParameters." << std::endl;
                    ret = AVERROR(ENOMEM);
                    goto end;
                }
                std::cout << "AVBufferSrcParameters: Will provide hw_frames_ctx with format "
                          << av_get_pix_fmt_name(AV_PIX_FMT_CUDA) << std::endl;
            } else {
                std::cerr << "Error: Using AV_PIX_FMT_CUDA, but dec_ctx_for_filter_props->hw_frames_ctx is NULL." << std::endl;
                ret = AVERROR(EINVAL);
                goto end;
            }
        } else {
            std::cerr << "Warning: Pixel format descriptor issue with AV_PIX_FMT_CUDA" << std::endl;
        }
    }

    std::cout << "Attempting to set AVBufferSrcParameters with hw_frames_ctx "
              << (src_par->hw_frames_ctx ? "set" : "NULL") << std::endl;

    ret = av_buffersrc_parameters_set(buffersrc_ctx_global, src_par);
    if (ret < 0) {
        std::cerr << "Cannot set AVBufferSrcParameters (hw_frames_ctx, etc.): " << av_error_to_string(ret) << std::endl;
        goto end;
    }
    std::cout << "AVBufferSrcParameters set successfully." << std::endl;

    ret = avfilter_graph_create_filter(&buffersink_ctx_global, buffersink_filter_ptr, "out", nullptr, nullptr, filter_graph_global);
    if (ret < 0) {
        std::cerr << "Cannot create buffer sink: " << av_error_to_string(ret) << std::endl;
        goto end;
    }

    ret = av_opt_set_int_list(buffersink_ctx_global, "pix_fmts", sink_pix_fmts, AV_PIX_FMT_NONE, AV_OPT_SEARCH_CHILDREN);
    if (ret < 0) {
        std::cerr << "Cannot set output pixel format for sink: " << av_error_to_string(ret) << std::endl;
        goto end;
    }

    outputs->name = av_strdup("in");
    outputs->filter_ctx = buffersrc_ctx_global;
    outputs->pad_idx = 0;
    outputs->next = nullptr;

    inputs->name = av_strdup("out");
    inputs->filter_ctx = buffersink_ctx_global;
    inputs->pad_idx = 0;
    inputs->next = nullptr;

    filter_spec_ss << "hwdownload,format=nv12,crop=w=" << CROP_W_val
                   << ":h=" << CROP_H_val << ":x=" << CROP_X_val << ":y=" << CROP_Y_val
                   << ",hwupload_cuda";
    filter_spec_str = filter_spec_ss.str();
    std::cout << "Filter Spec: " << filter_spec_str << std::endl;

    ret = avfilter_graph_parse_ptr(filter_graph_global, filter_spec_str.c_str(), &inputs, &outputs, nullptr);
    if (ret < 0) {
        std::cerr << "Cannot parse filter graph: " << av_error_to_string(ret) << std::endl;
        goto end;
    }

    ret = avfilter_graph_config(filter_graph_global, nullptr);
    if (ret < 0) {
        std::cerr << "Cannot configure filter graph: " << av_error_to_string(ret) << std::endl;
        goto end;
    }
    std::cout << "Filter graph initialized successfully." << std::endl;

end:
    if (src_par) {
        if (src_par->hw_frames_ctx) { // This was ref'd, so unref it
            av_buffer_unref(&src_par->hw_frames_ctx);
        }
        av_freep(&src_par); // Frees the AVBufferSrcParameters struct itself
    }
    avfilter_inout_free(&inputs);
    avfilter_inout_free(&outputs);
    return ret;
}

static int encode_write_frame(AVFrame *filt_frame, unsigned int stream_index, bool flush) {
    int ret = 0;
    AVPacket *enc_pkt = av_packet_alloc();
    if (!enc_pkt) {
        std::cerr << "Failed to allocate AVPacket for encoding." << std::endl;
        return AVERROR(ENOMEM);
    }

    // Send the frame to the encoder
    ret = avcodec_send_frame(encoder_ctx_global, filt_frame); // filt_frame can be NULL for flushing
    if (ret < 0) {
        if (ret == AVERROR_EOF && flush) { /* Expected EOF when flushing with NULL frame */ }
        else if (ret == AVERROR(EAGAIN) && !flush) { /* Expected EAGAIN if encoder needs more input */ }
        else {
            std::cerr << "Error sending frame to encoder: " << av_error_to_string(ret) << std::endl;
        }
        // Only treat unexpected errors as fatal for this step
        if (!((ret == AVERROR_EOF && flush) || (ret == AVERROR(EAGAIN) && !flush))) {
             goto end_encode;
        }
    }

    // Receive encoded packets from the encoder
    while (true) {
        ret = avcodec_receive_packet(encoder_ctx_global, enc_pkt);
        if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) {
            if (ret == AVERROR_EOF && flush) std::cout << "Encoder flushed completely." << std::endl;
            break; // Need more input or EOF reached
        } else if (ret < 0) {
            std::cerr << "Error during encoding (receiving packet): " << av_error_to_string(ret) << std::endl;
            goto end_encode; // Fatal error
        }

        // Packet successfully encoded
        enc_pkt->stream_index = stream_index;
        // Rescale PTS/DTS from encoder's timebase to output stream's timebase
        av_packet_rescale_ts(enc_pkt, encoder_ctx_global->time_base, output_format_ctx_global->streams[stream_index]->time_base);

        // Write the packet to the output file
        ret = av_interleaved_write_frame(output_format_ctx_global, enc_pkt);
        if (ret < 0) {
            std::cerr << "Error during writing frame to output: " << av_error_to_string(ret) << std::endl;
            goto end_encode; // Fatal error
        }
        av_packet_unref(enc_pkt); // Crucial to unref packet after writing
    }

end_encode:
    av_packet_free(&enc_pkt); // Free the allocated packet
    // Return 0 on successful EAGAIN (if not flushing) or EOF (if flushing), or if ret was 0 from send_frame and no packets.
    // Otherwise, return the error code.
    if ((ret == AVERROR(EAGAIN) && !flush) || (ret == AVERROR_EOF && flush) ) return 0;
    return ret < 0 ? ret : 0; // Ensure 0 is returned on non-fatal success cases too.
}


int main(int argc, char *argv[]) {
    const char *input_filename = nullptr;
    const char *output_filename_arg = default_output_filename_const; // Use const version

    if (argc < 3) {
        std::cerr << "Usage: " << argv[0] << " <input_video_file> <output_video_file> [crop_w crop_h crop_x crop_y]" << std::endl;
        std::cerr << "Example: " << argv[0] << " input.mp4 output_cropped.mp4 640 360 100 50" << std::endl;
        std::cerr << "Using default crop parameters if not specified." << std::endl;
        return (argc == 1) ? EXIT_SUCCESS : EXIT_FAILURE; // Allow running with no args for help
    }

    input_filename = argv[1];
    output_filename_arg = argv[2];

    if (argc >= 7) {
        try {
            CROP_W_val = std::stoi(argv[3]);
            CROP_H_val = std::stoi(argv[4]);
            CROP_X_val = std::stoi(argv[5]);
            CROP_Y_val = std::stoi(argv[6]);

            if (CROP_W_val <= 0 || CROP_H_val <= 0) {
                throw std::out_of_range("Crop width and height must be positive.");
            }
            if (CROP_X_val < 0 || CROP_Y_val < 0) {
                throw std::out_of_range("Crop X and Y offsets must be non-negative.");
            }
            std::cout << "Using custom crop parameters: W=" << CROP_W_val << " H=" << CROP_H_val
                      << " X=" << CROP_X_val << " Y=" << CROP_Y_val << std::endl;
        } catch (const std::invalid_argument& ia) {
            std::cerr << "Error: Invalid number format for crop parameter: " << ia.what() << std::endl;
            return EXIT_FAILURE;
        } catch (const std::out_of_range& oor) {
            std::cerr << "Error: Crop parameter out of range or invalid: " << oor.what() << std::endl;
            return EXIT_FAILURE;
        }
    } else if (argc > 3 && argc < 7) {
        std::cerr << "Warning: Incomplete crop parameters provided. Expected 4 crop values (W H X Y) or none." << std::endl;
        std::cout << "Using default crop parameters." << std::endl;
    } else { // argc == 3
        std::cout << "Using default crop parameters." << std::endl;
    }


    initialize_ffmpeg();

    AVFormatContext *input_format_ctx = nullptr;
    AVCodecContext *decoder_ctx = nullptr;
    const AVCodec *decoder = nullptr;
    AVBufferRef *decoder_hw_frames_ctx_ref = nullptr; // Specific to decoder instance
    int video_stream_index = -1;
    int ret = 0;

    AVFrame *frame = nullptr;     // Decoded frame
    AVFrame *filt_frame = nullptr; // Filtered frame

    try {
        // Open Input File
        if (avformat_open_input(&input_format_ctx, input_filename, nullptr, nullptr) != 0) {
            throw std::runtime_error("Could not open input file: " + std::string(input_filename));
        }
        if (avformat_find_stream_info(input_format_ctx, nullptr) < 0) {
            throw std::runtime_error("Could not find stream information.");
        }

        // Find Video Stream and Decoder
        AVCodecParameters *codecpar = nullptr;
        AVStream *video_avstream = nullptr;
        for (unsigned int i = 0; i < input_format_ctx->nb_streams; i++) {
            if (input_format_ctx->streams[i]->codecpar->codec_type == AVMEDIA_TYPE_VIDEO) {
                video_stream_index = i;
                video_avstream = input_format_ctx->streams[i];
                codecpar = video_avstream->codecpar;
                std::string preferred_decoder_name;
                // Prefer CUDA decoders
                switch (codecpar->codec_id) {
                    case AV_CODEC_ID_H264: preferred_decoder_name = "h264_cuvid"; break;
                    case AV_CODEC_ID_HEVC: preferred_decoder_name = "hevc_cuvid"; break;
                    case AV_CODEC_ID_VP9:  preferred_decoder_name = "vp9_cuvid";  break;
                    // Add other CUDA supported codecs if needed, e.g., AV1, MJPEG
                    case AV_CODEC_ID_AV1:  preferred_decoder_name = "av1_cuvid";  break;
                    default: break;
                }
                if (!preferred_decoder_name.empty()) {
                    decoder = avcodec_find_decoder_by_name(preferred_decoder_name.c_str());
                    if (decoder) std::cout << "Found preferred HW decoder: " << decoder->name << std::endl;
                }
                if (!decoder) { // Fallback to default decoder for the codec ID
                    decoder = avcodec_find_decoder(codecpar->codec_id);
                    if (decoder) std::cout << "Using fallback decoder: " << decoder->name << std::endl;
                }
                if (!decoder) throw std::runtime_error("Failed to find decoder for " + std::string(avcodec_get_name(codecpar->codec_id)));
                break;
            }
        }
        if (video_stream_index == -1 || !video_avstream) throw std::runtime_error("No video stream found in input file.");

        // Allocate Decoder Context
        decoder_ctx = avcodec_alloc_context3(decoder);
        if (!decoder_ctx) throw std::runtime_error("Failed to alloc decoder context.");
        if (avcodec_parameters_to_context(decoder_ctx, codecpar) < 0) {
            throw std::runtime_error("Failed to copy codec params to decoder context.");
        }

        // Set decoder properties not always copied by parameters_to_context
        decoder_ctx->width = codecpar->width;
        decoder_ctx->height = codecpar->height;
        if (video_avstream->time_base.num != 0 && video_avstream->time_base.den != 0) {
            decoder_ctx->time_base = video_avstream->time_base;
        } else if (video_avstream->r_frame_rate.num != 0 && video_avstream->r_frame_rate.den != 0) {
            decoder_ctx->time_base = av_inv_q(video_avstream->r_frame_rate);
        } else {
            decoder_ctx->time_base = (AVRational){1,25}; // Default if unknown
        }
        decoder_ctx->framerate = video_avstream->r_frame_rate; // For info
        decoder_ctx->sample_aspect_ratio = codecpar->sample_aspect_ratio.num ? codecpar->sample_aspect_ratio : (AVRational){1,1};


        // Setup HW Decoding (CUDA) if applicable
        bool is_hw_decoder = (std::string(decoder->name).find("cuvid") != std::string::npos ||
                              std::string(decoder->name).find("nvdec") != std::string::npos);
        if (is_hw_decoder) {
            if (av_hwdevice_ctx_create(&hw_device_ctx_ref_global, AV_HWDEVICE_TYPE_CUDA, nullptr, nullptr, 0) < 0) {
                throw std::runtime_error("Failed to create CUDA hw device context.");
            }
            decoder_ctx->hw_device_ctx = av_buffer_ref(hw_device_ctx_ref_global);
            if (!decoder_ctx->hw_device_ctx) {
                av_buffer_unref(&hw_device_ctx_ref_global); // Clean up if ref failed
                throw std::runtime_error("Failed to ref hw_device_ctx for decoder.");
            }
            decoder_ctx->get_format = get_hw_format; // Set callback for pixel format selection
            std::cout << "Set hw_device_ctx and get_format for HW decoder." << std::endl;
            // DO NOT set decoder_ctx->hw_frames_ctx here. Let avcodec_open2 handle it.
        }

        // Open Decoder
        if (avcodec_open2(decoder_ctx, decoder, nullptr) < 0) {
            throw std::runtime_error("Failed to open decoder: " + std::string(decoder->name));
        }

        // ────────────────────────────────────────────────────────────────────────────
        // Ensure we have a hw_frames_ctx for CUDA surfaces
        if (is_hw_decoder && decoder_ctx->pix_fmt == AV_PIX_FMT_CUDA && !decoder_ctx->hw_frames_ctx) {
            // 1) Allocate a HW frame pool from the CUDA device
            AVBufferRef *frames_ref = av_hwframe_ctx_alloc(hw_device_ctx_ref_global);
            if (!frames_ref)
                throw std::runtime_error("Failed to alloc hw_frames_ctx for decoder");

            // 2) Fill in parameters
            AVHWFramesContext *frames_ctx = (AVHWFramesContext*)frames_ref->data;
            frames_ctx->format            = AV_PIX_FMT_CUDA;     // GPU frames
            frames_ctx->sw_format         = AV_PIX_FMT_NV12;     // CPU‐side format if you ever download
            frames_ctx->width             = decoder_ctx->width;
            frames_ctx->height            = decoder_ctx->height;
            frames_ctx->initial_pool_size = 20;                  // tweak as needed

            // 3) Initialize the pool
            if (av_hwframe_ctx_init(frames_ref) < 0) {
                av_buffer_unref(&frames_ref);
                throw std::runtime_error("Failed to init hw_frames_ctx for decoder");
            }

            // 4) Attach it
            decoder_ctx->hw_frames_ctx = av_buffer_ref(frames_ref);
            av_buffer_unref(&frames_ref);
            std::cout << "Decoder hw_frames_ctx manually allocated and attached." << std::endl;
        }
        // ────────────────────────────────────────────────────────────────────────────

        // After avcodec_open2, if HW decoding is active, decoder_ctx->hw_frames_ctx should be set.
        if (is_hw_decoder) {
            if (decoder_ctx->pix_fmt == AV_PIX_FMT_CUDA) {
                if (decoder_ctx->hw_frames_ctx) {
                    std::cout << "Decoder successfully initialized with AV_PIX_FMT_CUDA and hw_frames_ctx is set by avcodec_open2." << std::endl;
                    // If you need decoder_hw_frames_ctx_ref for separate management/cleanup later:
                    decoder_hw_frames_ctx_ref = av_buffer_ref(decoder_ctx->hw_frames_ctx);
                    if (!decoder_hw_frames_ctx_ref) {
                        std::cerr << "Warning: Failed to ref decoder_ctx->hw_frames_ctx to decoder_hw_frames_ctx_ref." << std::endl;
                    }
                } else {
                    // This is the problematic state your logs point to now.
                    throw std::runtime_error("Decoder is HW and pix_fmt is CUDA, but hw_frames_ctx is NULL after avcodec_open2. HW init failed.");
                }
            } else {
                 throw std::runtime_error("Decoder is HW, but pix_fmt is not CUDA after avcodec_open2. get_format did not work as expected.");
            }
        }

        // Update context properties that might change after open (e.g., actual pix_fmt)
        // decoder_ctx->width, height, sample_aspect_ratio should be correct from params or updated by open.

        std::cout << "Decoder " << decoder->name << " opened. Actual properties: "
                  << decoder_ctx->width << "x" << decoder_ctx->height
                  << " fmt: " << av_get_pix_fmt_name(decoder_ctx->pix_fmt)
                  << " tb: " << decoder_ctx->time_base.num << "/" << decoder_ctx->time_base.den << std::endl;

        // Validate crop parameters against actual video dimensions
        if (CROP_X_val + CROP_W_val > decoder_ctx->width || CROP_Y_val + CROP_H_val > decoder_ctx->height) {
            std::cerr << "Warning: Crop dimensions (X+W or Y+H) exceed video dimensions ("
                      << decoder_ctx->width << "x" << decoder_ctx->height << ")." << std::endl;
            // You might choose to throw an error here or adjust crop values.
            // For now, we'll let FFmpeg handle it, which might result in an error or unexpected crop.
        }


        // Setup Output Format Context
        avformat_alloc_output_context2(&output_format_ctx_global, nullptr, nullptr, output_filename_arg);
        if (!output_format_ctx_global) throw std::runtime_error("Could not create output context for: " + std::string(output_filename_arg));

        // Setup Encoder (h264_nvenc)
        const AVCodec *encoder_codec = avcodec_find_encoder_by_name("h264_nvenc");
        if (!encoder_codec) throw std::runtime_error("h264_nvenc encoder not found. Ensure NVIDIA drivers and FFmpeg are correctly installed.");

        AVStream *out_stream = avformat_new_stream(output_format_ctx_global, nullptr);
        if (!out_stream) throw std::runtime_error("Failed allocating output stream.");

        encoder_ctx_global = avcodec_alloc_context3(encoder_codec);
        if (!encoder_ctx_global) throw std::runtime_error("Failed to alloc encoder context (h264_nvenc).");

        encoder_ctx_global->codec_type = AVMEDIA_TYPE_VIDEO;
        encoder_ctx_global->width = CROP_W_val;
        encoder_ctx_global->height = CROP_H_val;
        // NVENC works with CUDA frames directly or common YUV formats if hw_frames_ctx is set up
        encoder_ctx_global->pix_fmt = AV_PIX_FMT_CUDA;

        // Timebase: Encoder timebase should match the output stream's timebase for simplicity.
        // A common high-resolution timebase for video is 1/90000.
        // Or, match decoder's framerate if possible.
        if (video_avstream->r_frame_rate.num != 0 && video_avstream->r_frame_rate.den != 0) {
            encoder_ctx_global->framerate = video_avstream->r_frame_rate;
            encoder_ctx_global->time_base = av_inv_q(video_avstream->r_frame_rate);
        } else { // Fallback if source framerate is unknown
            encoder_ctx_global->framerate = (AVRational){25, 1}; // Default to 25 FPS
            encoder_ctx_global->time_base = (AVRational){1, 25};
        }
        out_stream->time_base = encoder_ctx_global->time_base; // Ensure stream and encoder context match

        encoder_ctx_global->bit_rate = 2 * 1000 * 1000; // 2 Mbps, make configurable if needed

        // Set NVENC preset for performance (p1 is usually fastest, check NVENC docs for options)
        // Options: "default", "slow", "medium", "fast", "hp", "hq", "bd", "ll", "llhq", "llhp", "lossless", "losslesshp"
        // P-state mapping: p1 (fastest) to p7 (best quality)
        if (av_opt_set(encoder_ctx_global, "preset", "p1", 0) < 0) {
            std::cerr << "Warning: Failed to set NVENC preset." << std::endl;
        }
        // You might also want to set profile (e.g., "main", "high") or other options.
        // av_opt_set(encoder_ctx_global, "profile", "high", 0);


        if (output_format_ctx_global->oformat->flags & AVFMT_GLOBALHEADER) {
            encoder_ctx_global->flags |= AV_CODEC_FLAG_GLOBAL_HEADER;
        }

        // Prepare a temporary decoder context properties for filter initialization
        // This context describes the data entering the filter graph (i.e., output of the decoder)
        AVPixelFormat temp_decoder_pix_fmt_for_filter_init;
        if (is_hw_decoder) {
             std::cout << "Decoder is HW. For filter init, input pix_fmt is AV_PIX_FMT_CUDA." << std::endl;
             temp_decoder_pix_fmt_for_filter_init = AV_PIX_FMT_CUDA;
        } else {
            temp_decoder_pix_fmt_for_filter_init = decoder_ctx->pix_fmt;
            if (temp_decoder_pix_fmt_for_filter_init == AV_PIX_FMT_NONE) {
                temp_decoder_pix_fmt_for_filter_init = (AVPixelFormat)codecpar->format; // Fallback
                 std::cout << "SW Decoder pix_fmt is NONE after open, using codecpar->format for filter: " << av_get_pix_fmt_name(temp_decoder_pix_fmt_for_filter_init) << std::endl;
            }
            if (temp_decoder_pix_fmt_for_filter_init == AV_PIX_FMT_NONE) { // Ultimate fallback
                temp_decoder_pix_fmt_for_filter_init = AV_PIX_FMT_YUV420P;
                std::cout << "Warning: SW Decoder pix_fmt still unknown, defaulting to YUV420P for filter init." << std::endl;
            }
        }

        AVCodecContext* temp_dec_ctx_for_filter = avcodec_alloc_context3(nullptr); // No need to pass 'decoder' here
        if(!temp_dec_ctx_for_filter) throw std::runtime_error("Failed to alloc temp decoder ctx for filter init");

        temp_dec_ctx_for_filter->width = decoder_ctx->width;
        temp_dec_ctx_for_filter->height = decoder_ctx->height;
        temp_dec_ctx_for_filter->time_base = decoder_ctx->time_base; // Use actual decoder time_base
        temp_dec_ctx_for_filter->sample_aspect_ratio = decoder_ctx->sample_aspect_ratio;
        temp_dec_ctx_for_filter->pix_fmt = temp_decoder_pix_fmt_for_filter_init;

        std::cout << "Using time_base for filter init: " << temp_dec_ctx_for_filter->time_base.num << "/" << temp_dec_ctx_for_filter->time_base.den << std::endl;

        if(is_hw_decoder) {
            // The filter graph will operate on frames from hw_device_ctx_ref_global
            // and specifically using frames compatible with decoder_ctx->hw_frames_ctx
            if (decoder_ctx->hw_frames_ctx) {
                 temp_dec_ctx_for_filter->hw_frames_ctx = av_buffer_ref(decoder_ctx->hw_frames_ctx);
                 if (!temp_dec_ctx_for_filter->hw_frames_ctx) {
                    avcodec_free_context(&temp_dec_ctx_for_filter);
                    throw std::runtime_error("Failed to ref decoder_ctx->hw_frames_ctx for temp_dec_ctx_for_filter.");
                 }
            } else {
                // This shouldn't happen if HW decoder setup was successful
                std::cerr << "Warning: is_hw_decoder is true, but decoder_ctx->hw_frames_ctx is NULL." << std::endl;
            }
            // sw_pix_fmt isn't directly used by buffersrc, but good to be aware of
            // temp_dec_ctx_for_filter->sw_pix_fmt = decoder_ctx->sw_pix_fmt ? decoder_ctx->sw_pix_fmt : AV_PIX_FMT_NV12;
        }

        // Initialize Filters
        if (init_filters(temp_dec_ctx_for_filter) < 0) {
            if(temp_dec_ctx_for_filter->hw_frames_ctx) av_buffer_unref(&temp_dec_ctx_for_filter->hw_frames_ctx);
            // temp_dec_ctx_for_filter->hw_device_ctx was not set, so no unref needed for it.
            avcodec_free_context(&temp_dec_ctx_for_filter);
            throw std::runtime_error("Could not initialize filters.");
        }
        // Clean up temp_dec_ctx_for_filter as its info has been used by init_filters
        if(temp_dec_ctx_for_filter->hw_frames_ctx) av_buffer_unref(&temp_dec_ctx_for_filter->hw_frames_ctx);
        avcodec_free_context(&temp_dec_ctx_for_filter);


        // Setup Encoder's hw_frames_ctx (must be compatible with buffersink output)
        if (encoder_ctx_global->pix_fmt == AV_PIX_FMT_CUDA) {
            // Always create a fresh hw_frames_ctx for the encoder
            AVBufferRef* new_enc_hw_frames_ctx = av_hwframe_ctx_alloc(hw_device_ctx_ref_global);
            if (!new_enc_hw_frames_ctx)
                throw std::runtime_error("Failed to alloc hw_frames_ctx for encoder");
            AVHWFramesContext* enc_frames_data = (AVHWFramesContext*)new_enc_hw_frames_ctx->data;
            enc_frames_data->format            = AV_PIX_FMT_CUDA;
            enc_frames_data->sw_format         = AV_PIX_FMT_NV12;
            enc_frames_data->width             = encoder_ctx_global->width;
            enc_frames_data->height            = encoder_ctx_global->height;
            enc_frames_data->initial_pool_size = 20;
            if (av_hwframe_ctx_init(new_enc_hw_frames_ctx) < 0) {
                av_buffer_unref(&new_enc_hw_frames_ctx);
                throw std::runtime_error("Failed to init hw_frames_ctx for encoder");
            }
            encoder_ctx_global->hw_frames_ctx = new_enc_hw_frames_ctx;
            std::cout << "Created hw_frames_ctx for encoder." << std::endl;
        }

        // Open Encoder
        if (avcodec_open2(encoder_ctx_global, encoder_codec, nullptr) < 0) {
            throw std::runtime_error("Cannot open video encoder: " + std::string(encoder_codec->name));
        }
        std::cout << "Encoder " << encoder_codec->name << " opened. Expecting "
                  << av_get_pix_fmt_name(encoder_ctx_global->pix_fmt)
                  << " " << encoder_ctx_global->width << "x" << encoder_ctx_global->height << std::endl;

        // Copy encoder parameters to output stream
        if (avcodec_parameters_from_context(out_stream->codecpar, encoder_ctx_global) < 0) {
            throw std::runtime_error("Failed to copy encoder params to output stream.");
        }

        // Open Output File and Write Header
        if (!(output_format_ctx_global->oformat->flags & AVFMT_NOFILE)) {
            if (avio_open(&output_format_ctx_global->pb, output_filename_arg, AVIO_FLAG_WRITE) < 0) {
                throw std::runtime_error("Could not open output file: " + std::string(output_filename_arg));
            }
        }
        if (avformat_write_header(output_format_ctx_global, nullptr) < 0) {
            throw std::runtime_error("Error occurred when writing output file header.");
        }
        std::cout << "Output file opened and header written: " << output_filename_arg << std::endl;

        // Allocate frames for decoding and filtering
        frame = av_frame_alloc();
        filt_frame = av_frame_alloc();
        if (!frame || !filt_frame) throw std::runtime_error("Cannot allocate AVFrame.");

        int frame_count = 0;
        long long last_input_pts = AV_NOPTS_VALUE;

        std::cout << "Starting transcoding loop..." << std::endl;
        AVPacket *packet = av_packet_alloc(); // Allocate packet for reading input
        if (!packet) throw std::runtime_error("Failed to allocate AVPacket for reading.");

        // Main Processing Loop
        while (av_read_frame(input_format_ctx, packet) >= 0) {
            if (packet->stream_index == video_stream_index) {
                ret = avcodec_send_packet(decoder_ctx, packet);
                if (ret < 0) {
                    std::cerr << "Error sending packet for decoding: " << av_error_to_string(ret) << std::endl;
                    break; // Exit loop on send error
                }

                while (true) { // Receive all frames from this packet
                    ret = avcodec_receive_frame(decoder_ctx, frame);
                    if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) break; // Need more data or end of stream
                    if (ret < 0) {
                        std::cerr << "Error during decoding (receiving frame): " << av_error_to_string(ret) << std::endl;
                        goto end_processing_loop; // Fatal error
                    }

                    // For HW decoded frames, ensure hw_frames_ctx is set
                    if (frame->format == AV_PIX_FMT_CUDA && !frame->hw_frames_ctx) {
                        if (decoder_ctx->hw_frames_ctx) {
                           frame->hw_frames_ctx = av_buffer_ref(decoder_ctx->hw_frames_ctx);
                           if (!frame->hw_frames_ctx) {
                               std::cerr << "Warning: Failed to ref decoder_ctx->hw_frames_ctx to frame in loop." << std::endl;
                               // This could be problematic for filters
                           }
                        } else {
                             // This should ideally not happen if HW decoding is active and setup correctly.
                             std::cerr << "CRITICAL Warning: Decoded CUDA frame is missing hw_frames_ctx and decoder_ctx also has none!" << std::endl;
                        }
                    }

                    // PTS handling (simple approach for monotonicity)
                    if (frame->pts == AV_NOPTS_VALUE) frame->pts = frame->pkt_dts; // Use DTS if PTS is not set
                    if (frame->pts != AV_NOPTS_VALUE) {
                        if (last_input_pts != AV_NOPTS_VALUE && frame->pts <= last_input_pts) {
                             frame->pts = last_input_pts + 1; // Ensure PTS is monotonic
                        }
                        last_input_pts = frame->pts;
                    } else {
                        // If still no PTS, might need a frame counter based approach, but less ideal
                        // For now, FFmpeg filters might handle this or use time_base.
                        // Or assign based on frame_count if strictly necessary and time_base is known.
                    }


                    if (frame_count == 0) { // Log first decoded frame details
                        std::cout << "First decoded frame format: " << av_get_pix_fmt_name((AVPixelFormat)frame->format)
                                  << " (width " << frame->width << " height " << frame->height << " pts " << frame->pts
                                  << " hw_ctx: " << (frame->hw_frames_ctx ? "Set" : "NULL") << ")" << std::endl;
                    }

                    // Feed frame to filter graph
                    if (av_buffersrc_add_frame_flags(buffersrc_ctx_global, frame, AV_BUFFERSRC_FLAG_KEEP_REF) < 0) {
                        std::cerr << "Error while feeding the filtergraph." << std::endl;
                        av_frame_unref(frame); // Unref if not consumed by filter
                        break;
                    }

                    // Get filtered frames
                    while (true) {
                        ret = av_buffersink_get_frame(buffersink_ctx_global, filt_frame);
                        if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) break;
                        if (ret < 0) {
                             std::cerr << "Error while receiving frame from filtergraph: " << av_error_to_string(ret) << std::endl;
                             goto end_processing_loop;
                        }

                        if (frame_count == 0 && frame_count < 1) { // Log first filtered frame
                             std::cout << "First filtered frame format: " << av_get_pix_fmt_name((AVPixelFormat)filt_frame->format)
                                       << " (width " << filt_frame->width << " height " << filt_frame->height << " pts " << filt_frame->pts
                                       << " hw_ctx: " << (filt_frame->hw_frames_ctx ? "Set" : "NULL") << ")" << std::endl;
                        }

                        // Ensure filtered CUDA frames have hw_frames_ctx for the encoder
                         if (filt_frame->format == AV_PIX_FMT_CUDA && !filt_frame->hw_frames_ctx && encoder_ctx_global->hw_frames_ctx) {
                             filt_frame->hw_frames_ctx = av_buffer_ref(encoder_ctx_global->hw_frames_ctx);
                             if(!filt_frame->hw_frames_ctx) std::cerr << "Warning: Failed to ref encoder_ctx->hw_frames_ctx to filt_frame." << std::endl;
                        } else if (filt_frame->format == AV_PIX_FMT_CUDA && !filt_frame->hw_frames_ctx) {
                             std::cerr << "Error: Filtered CUDA frame has no hw_frames_ctx, and encoder_ctx has no suitable one." << std::endl;
                             // This could lead to encoder failure.
                        }

                        // If filter messed up PTS, try to restore from original frame's PTS
                        if (filt_frame->pts == AV_NOPTS_VALUE) {
                            filt_frame->pts = frame->pts; // Or a rescaled version if timebases differ
                        }

                        // Encode and write filtered frame
                        if (encode_write_frame(filt_frame, out_stream->index, false) < 0) {
                            av_frame_unref(filt_frame);
                            goto end_processing_loop;
                        }
                        av_frame_unref(filt_frame); // Crucial
                    }
                    av_frame_unref(frame); // Crucial if AV_BUFFERSRC_FLAG_KEEP_REF was used
                    frame_count++;
                    if (frame_count % 100 == 0) std::cout << "Processed " << frame_count << " input frames." << std::endl;
                }
            }
            av_packet_unref(packet); // Unref packet after processing
        }
    end_processing_loop:;
        av_packet_free(&packet); // Free the allocated packet structure

        std::cout << "Flushing pipeline components..." << std::endl;

        // Flush Decoder
        std::cout << "Flushing decoder..." << std::endl;
        ret = avcodec_send_packet(decoder_ctx, nullptr); // Send NULL to flush decoder
        // Process remaining decoded frames
        while (ret >= 0) {
            ret = avcodec_receive_frame(decoder_ctx, frame);
            if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) break;
            if (ret < 0) { std::cerr << "Error flushing decoder final frames: " << av_error_to_string(ret) << std::endl; break;}

            if (frame->format == AV_PIX_FMT_CUDA && !frame->hw_frames_ctx && decoder_ctx->hw_frames_ctx) {
                frame->hw_frames_ctx = av_buffer_ref(decoder_ctx->hw_frames_ctx);
            }
            // PTS handling for flushed frames might be needed if not already set
            if (frame->pts == AV_NOPTS_VALUE && last_input_pts != AV_NOPTS_VALUE) {
                frame->pts = last_input_pts + 1; // Simple increment
                last_input_pts = frame->pts;
            }


            if (av_buffersrc_add_frame_flags(buffersrc_ctx_global, frame, AV_BUFFERSRC_FLAG_KEEP_REF) < 0) {
                 std::cerr << "Error feeding flushed decoder frame to filtergraph." << std::endl;
                 av_frame_unref(frame); break;
            }
            while (true) { // Get frames from filter graph
                ret = av_buffersink_get_frame(buffersink_ctx_global, filt_frame);
                if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) break;
                if (ret < 0) { std::cerr << "Error getting frame from filtergraph during decoder flush." << std::endl; av_frame_unref(frame); goto end_flush_filter;}

                if (filt_frame->format == AV_PIX_FMT_CUDA && !filt_frame->hw_frames_ctx && encoder_ctx_global->hw_frames_ctx) {
                     filt_frame->hw_frames_ctx = av_buffer_ref(encoder_ctx_global->hw_frames_ctx);
                }
                if (filt_frame->pts == AV_NOPTS_VALUE) filt_frame->pts = frame->pts; // Propagate PTS

                encode_write_frame(filt_frame, out_stream->index, false);
                av_frame_unref(filt_frame);
            }
            av_frame_unref(frame);
        }

    end_flush_filter:
        // Flush Filter Graph
        std::cout << "Flushing filter graph..." << std::endl;
        if (av_buffersrc_add_frame_flags(buffersrc_ctx_global, nullptr, 0) < 0) { // Send NULL to flush buffersrc
             std::cerr << "Error sending flush signal to buffer source." << std::endl;
        }
        while (true) { // Get remaining frames from buffersink
            ret = av_buffersink_get_frame(buffersink_ctx_global, filt_frame);
            if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) break;
            if (ret < 0) { std::cerr << "Error flushing sink final frames: " << av_error_to_string(ret) << std::endl; break;}

            if (filt_frame->format == AV_PIX_FMT_CUDA && !filt_frame->hw_frames_ctx && encoder_ctx_global->hw_frames_ctx) {
                filt_frame->hw_frames_ctx = av_buffer_ref(encoder_ctx_global->hw_frames_ctx);
            }
            // PTS for these final filtered frames might need careful handling if not set by filter.
            // Often, they carry over from the last valid input frame's PTS or are marked by filter.

            encode_write_frame(filt_frame, out_stream->index, false); // Not flushing encoder yet
            av_frame_unref(filt_frame);
        }

        // Flush Encoder
        std::cout << "Flushing encoder..." << std::endl;
        encode_write_frame(nullptr, out_stream->index, true); // Pass NULL frame and flush=true

        // Write Trailer and Close Output
        av_write_trailer(output_format_ctx_global);
        std::cout << "Transcoding finished. Total frames processed: " << frame_count << ". Output: " << output_filename_arg << std::endl;

    } catch (const std::runtime_error &e) {
        std::cerr << "Runtime Error: " << e.what() << std::endl;
        ret = EXIT_FAILURE; // Indicate error
    } catch (...) {
        std::cerr << "An unknown error occurred." << std::endl;
        ret = EXIT_FAILURE;
    }

    // --- Cleanup ---
    std::cout << "Cleaning up resources..." << std::endl;
    av_frame_free(&frame);
    av_frame_free(&filt_frame);

    if (filter_graph_global) {
        // Individual filter contexts (buffersrc_ctx_global, buffersink_ctx_global) are part of the graph
        // and freed when the graph is freed. No need to free them separately.
        avfilter_graph_free(&filter_graph_global);
    }
    // hw_device_ctx_ref_global is unref'd at the very end
    // decoder_hw_frames_ctx_ref is unref'd after decoder_ctx is done with it

    if (decoder_ctx) {
        if(decoder_ctx->hw_frames_ctx) av_buffer_unref(&decoder_ctx->hw_frames_ctx); // hw_frames_ctx was from decoder_hw_frames_ctx_ref
        // decoder_ctx->hw_device_ctx was a ref from hw_device_ctx_ref_global, unref it
        if(decoder_ctx->hw_device_ctx) av_buffer_unref(&decoder_ctx->hw_device_ctx);
        avcodec_free_context(&decoder_ctx);
    }
    if (decoder_hw_frames_ctx_ref) av_buffer_unref(&decoder_hw_frames_ctx_ref); // Original ref for decoder's frames

    if (encoder_ctx_global) {
        if(encoder_ctx_global->hw_frames_ctx) av_buffer_unref(&encoder_ctx_global->hw_frames_ctx);
        // Encoder did not directly take hw_device_ctx, it used hw_device_ctx_ref_global via its hw_frames_ctx
        avcodec_free_context(&encoder_ctx_global);
    }

    if (input_format_ctx) avformat_close_input(&input_format_ctx);

    if (output_format_ctx_global) {
        if (!(output_format_ctx_global->oformat->flags & AVFMT_NOFILE) && output_format_ctx_global->pb) {
            avio_closep(&output_format_ctx_global->pb);
        }
        avformat_free_context(output_format_ctx_global);
    }

    if (hw_device_ctx_ref_global) av_buffer_unref(&hw_device_ctx_ref_global); // Final unref of global device context

    avformat_network_deinit(); // Corresponds to avformat_network_init()
    std::cout << "Cleanup finished." << std::endl;

    return ret == 0 ? EXIT_SUCCESS : EXIT_FAILURE;
}
