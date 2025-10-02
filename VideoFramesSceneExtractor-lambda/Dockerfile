###############################################################################
# 1) Builder stage: grab a static ffmpeg build on Amazon Linux
###############################################################################
FROM amazonlinux:2 AS build

# Install curl, xz, and tar so we can unpack the ffmpeg static build
RUN yum install -y curl xz tar && \
    curl -fsSL https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz \
      -o /tmp/ffmpeg.tar.xz && \
    tar -xJf /tmp/ffmpeg.tar.xz -C /tmp && \
    cp /tmp/ffmpeg-*-amd64-static/ffmpeg  /tmp/ffmpeg && \
    cp /tmp/ffmpeg-*-amd64-static/ffprobe /tmp/ffprobe


###############################################################################
# 2) Final Lambda image
###############################################################################
FROM public.ecr.aws/lambda/python:3.12

# Copy in the ffmpeg + ffprobe binaries from builder
COPY --from=build /tmp/ffmpeg  /usr/local/bin/ffmpeg
COPY --from=build /tmp/ffprobe /usr/local/bin/ffprobe
RUN chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe

# Install Python deps
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy your code & .env
COPY .env            ${LAMBDA_TASK_ROOT}/
COPY lambda_function.py ${LAMBDA_TASK_ROOT}/

# Lambda entrypoint
CMD [ "lambda_function.lambda_handler" ]
