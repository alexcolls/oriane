#include <iostream>
#include <string>
#include <stdexcept> // For std::runtime_error

// FFmpeg headers
extern "C" {
#include <libavformat/avformat.h>
#include <libavcodec/avcodec.h>
#include <libavutil/hwcontext.h>
#include <libavutil/hwcontext_cuda.h> // For CUDA specific hardware context
#include <libavutil/pixfmt.h>
#include <libavutil/pixdesc.h> // For av_get_pix_fmt_name
#include <libavutil/opt.h>     // For av_opt_set
}

// Helper function to convert AVError to string
static std::string av_error_to_string(int errnum) {
    char errbuf[AV_ERROR_MAX_STRING_SIZE];
    av_strerror(errnum, errbuf, AV_ERROR_MAX_STRING_SIZE);
    return std::string(errbuf);
}

// Global initialization for FFmpeg (call once)
static void initialize_ffmpeg() {
    // av_register_all(); // Deprecated in newer FFmpeg versions
    avformat_network_init(); // Useful if dealing with network streams, good practice
    std::cout << "FFmpeg initialized." << std::endl;
}

// Function to find a hardware decoder configuration
static enum AVPixelFormat get_hw_format(AVCodecContext *ctx, const enum AVPixelFormat *pix_fmts) {
    const enum AVPixelFormat *p;
    for (p = pix_fmts; *p != -1; p++) {
        if (*p == AV_PIX_FMT_CUDA) { // We are looking for CUDA pixel format
            std::cout << "Found AV_PIX_FMT_CUDA in supported formats." << std::endl;
            return *p;
        }
    }
    std::cerr << "Failed to get AV_PIX_FMT_CUDA. This means the decoder doesn't support CUDA output directly." << std::endl;
    return AV_PIX_FMT_NONE;
}


int main(int argc, char *argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <input_video_file>" << std::endl;
        return 1;
    }
    const char *input_filename = argv[1];

    initialize_ffmpeg();

    AVFormatContext *format_ctx = nullptr;
    AVCodecContext *decoder_ctx = nullptr;
    const AVCodec *decoder = nullptr; // Corrected: Added const
    AVBufferRef *hw_device_ctx = nullptr;
    int video_stream_index = -1;

    try {
        // 1. Open video file
        if (avformat_open_input(&format_ctx, input_filename, nullptr, nullptr) != 0) {
            throw std::runtime_error("Could not open input file: " + std::string(input_filename));
        }
        std::cout << "Input file opened." << std::endl;

        // 2. Retrieve stream information
        if (avformat_find_stream_info(format_ctx, nullptr) < 0) {
            throw std::runtime_error("Could not find stream information.");
        }
        std::cout << "Stream information found." << std::endl;

        // 3. Find the first video stream and its decoder
        for (unsigned int i = 0; i < format_ctx->nb_streams; i++) {
            if (format_ctx->streams[i]->codecpar->codec_type == AVMEDIA_TYPE_VIDEO) {
                video_stream_index = i;
                AVCodecParameters *codecpar = format_ctx->streams[i]->codecpar;

                // Try to find hardware decoder first
                std::string decoder_name_str;
                switch (codecpar->codec_id) {
                    case AV_CODEC_ID_H264: decoder_name_str = "h264_cuvid"; break;
                    case AV_CODEC_ID_HEVC: decoder_name_str = "hevc_cuvid"; break;
                    case AV_CODEC_ID_VP9:  decoder_name_str = "vp9_cuvid";  break;
                    case AV_CODEC_ID_AV1:  decoder_name_str = "av1_cuvid";  break; // Or av1_nvdec
                    default:
                        std::cerr << "Unsupported codec for CUVID: " << avcodec_get_name(codecpar->codec_id) << std::endl;
                        // Fallback to software decoder or error out
                        decoder = avcodec_find_decoder(codecpar->codec_id); // Corrected: Assignment to const AVCodec*
                        if (!decoder) {
                             throw std::runtime_error("Unsupported codec: " + std::string(avcodec_get_name(codecpar->codec_id)));
                        }
                        std::cout << "Using software decoder: " << decoder->name << std::endl;
                        break;
                }

                if (!decoder_name_str.empty()) {
                    decoder = avcodec_find_decoder_by_name(decoder_name_str.c_str()); // Corrected: Assignment to const AVCodec*
                    if (decoder) {
                        std::cout << "Found hardware decoder: " << decoder->name << std::endl;
                    } else {
                        std::cerr << "Could not find hardware decoder: " << decoder_name_str << ". Trying software." << std::endl;
                        decoder = avcodec_find_decoder(codecpar->codec_id); // Corrected: Assignment to const AVCodec*
                         if (!decoder) {
                             throw std::runtime_error("Unsupported codec (even software): " + std::string(avcodec_get_name(codecpar->codec_id)));
                        }
                        std::cout << "Using software decoder: " << decoder->name << std::endl;
                    }
                }
                break; // Use the first video stream found
            }
        }

        if (video_stream_index == -1) {
            throw std::runtime_error("Could not find a video stream in the input file.");
        }

        // 4. Allocate a codec context for the decoder
        decoder_ctx = avcodec_alloc_context3(decoder);
        if (!decoder_ctx) {
            throw std::runtime_error("Failed to allocate the decoder context.");
        }

        // Copy codec parameters from input stream to output codec context
        if (avcodec_parameters_to_context(decoder_ctx, format_ctx->streams[video_stream_index]->codecpar) < 0) {
            throw std::runtime_error("Failed to copy codec parameters to decoder context.");
        }

        // 5. Initialize hardware device and context if using a CUVID decoder
        bool is_hw_decoder = (decoder && (std::string(decoder->name).find("cuvid") != std::string::npos ||
                                          std::string(decoder->name).find("nvdec") != std::string::npos));

        if (is_hw_decoder) {
            std::cout << "Attempting to initialize CUDA hardware context." << std::endl;
            int err = av_hwdevice_ctx_create(&hw_device_ctx, AV_HWDEVICE_TYPE_CUDA, nullptr, nullptr, 0);
            if (err < 0) {
                throw std::runtime_error("Failed to create CUDA hardware device context: " + av_error_to_string(err));
            }
            std::cout << "CUDA hardware context created." << std::endl;
            decoder_ctx->hw_device_ctx = av_buffer_ref(hw_device_ctx);
            if (!decoder_ctx->hw_device_ctx) {
                 throw std::runtime_error("Failed to assign hw_device_ctx to decoder context.");
            }
            // Set the pixel format callback to get AV_PIX_FMT_CUDA
            decoder_ctx->get_format = get_hw_format;
            std::cout << "Set get_format callback for CUDA." << std::endl;
        }


        // 6. Open the decoder
        // avcodec_open2 expects a non-const AVCodec*.
        // However, the decoder variable is now const AVCodec*.
        // We need to cast away const for this specific function call.
        // This is generally safe if avcodec_open2 doesn't modify the AVCodec structure itself,
        // which is typically the case (it uses it to initialize the context).
        // Alternatively, one might need to find the decoder again without const if a non-const version is strictly needed
        // but for avcodec_open2, this cast is a common practice when the original find functions return const.
        if (avcodec_open2(decoder_ctx, const_cast<AVCodec*>(decoder), nullptr) < 0) {
            throw std::runtime_error("Failed to open decoder.");
        }
        std::cout << "Decoder opened successfully." << std::endl;

        // --- At this point, the decoder is initialized. ---
        // --- We can now read packets and send them for decoding. ---

        AVPacket *packet = av_packet_alloc();
        if (!packet) throw std::runtime_error("Failed to allocate AVPacket.");

        AVFrame *frame = av_frame_alloc();
        if (!frame) throw std::runtime_error("Failed to allocate AVFrame.");

        AVFrame *sw_frame = nullptr; // For frames downloaded from GPU if needed
        if (is_hw_decoder) { // Only allocate if we expect HW frames
            sw_frame = av_frame_alloc();
             if (!sw_frame) throw std::runtime_error("Failed to allocate sw_frame for HW decoding.");
        }


        std::cout << "Starting to read packets and decode frames..." << std::endl;
        int frame_count = 0;
        const int max_frames_to_decode = 5; // Let's decode a few frames for testing

        while (av_read_frame(format_ctx, packet) >= 0) {
            if (packet->stream_index == video_stream_index) {
                int ret = avcodec_send_packet(decoder_ctx, packet);
                if (ret < 0) {
                    std::cerr << "Error sending a packet for decoding: " << av_error_to_string(ret) << std::endl;
                    break;
                }

                while (ret >= 0) {
                    ret = avcodec_receive_frame(decoder_ctx, frame);
                    if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) {
                        break; // Need more input or end of stream
                    } else if (ret < 0) {
                        std::cerr << "Error during decoding: " << av_error_to_string(ret) << std::endl;
                        goto end_loop; // Error, exit packet reading loop
                    }

                    // Frame successfully decoded
                    frame_count++;
                    std::cout << "Decoded frame " << frame_count << " (pts: " << frame->pts << ")";
                    if (frame->format == AV_PIX_FMT_CUDA) {
                        std::cout << " - Format: AV_PIX_FMT_CUDA (on GPU)" << std::endl;
                        // To access pixel data, you'd need to download it from GPU
                        // Example:
                        // if (sw_frame) { // Ensure sw_frame was allocated
                        //     if (av_hwframe_transfer_data(sw_frame, frame, 0) >= 0) {
                        //         std::cout << "   -> Transferred to CPU, format: " << av_get_pix_fmt_name((AVPixelFormat)sw_frame->format) << std::endl;
                        //         // ... process sw_frame ...
                        //     } else {
                        //         std::cerr << "   -> Failed to transfer HW frame to CPU." << std::endl;
                        //     }
                        //     av_frame_unref(sw_frame); // Important to unref after use
                        // }
                    } else {
                        std::cout << " - Format: " << av_get_pix_fmt_name((AVPixelFormat)frame->format) << " (on CPU)" << std::endl;
                    }

                    av_frame_unref(frame); // Release the frame reference

                    if (frame_count >= max_frames_to_decode) {
                        goto end_loop;
                    }
                }
            }
            av_packet_unref(packet); // Release the packet reference
        }
    end_loop:;

        std::cout << "Finished decoding. Total frames decoded: " << frame_count << std::endl;

        // Cleanup
        av_packet_free(&packet);
        av_frame_free(&frame);
        if (sw_frame) av_frame_free(&sw_frame);

    } catch (const std::runtime_error &e) {
        std::cerr << "Error: " << e.what() << std::endl;
        // Ensure cleanup even on exception
        if (decoder_ctx) avcodec_free_context(&decoder_ctx); // Free context if allocated
        if (format_ctx) avformat_close_input(&format_ctx);   // Close input if opened
        if (hw_device_ctx) av_buffer_unref(&hw_device_ctx); // Unref hw context if created
        avformat_network_deinit();
        return 1; // Indicate error
    }

    // Final cleanup (if no exception occurred or for partially successful states)
    if (decoder_ctx) avcodec_free_context(&decoder_ctx);
    if (format_ctx) avformat_close_input(&format_ctx);
    if (hw_device_ctx) av_buffer_unref(&hw_device_ctx);

    avformat_network_deinit(); // Counterpart to avformat_network_init()

    return 0;
}
