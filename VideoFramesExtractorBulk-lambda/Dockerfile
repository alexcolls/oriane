# Official AWS Lambda Node.js 18 base image
FROM public.ecr.aws/lambda/nodejs:18

# Install tar, curl, and xz (needed to extract .tar.xz)
RUN yum update -y && yum install -y tar curl xz

# Download and extract FFmpeg (using a static build)
RUN curl -L -o ffmpeg.tar.xz https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz \
  && tar -xJf ffmpeg.tar.xz --strip-components=1 -C /usr/local/bin ffmpeg-*-static/ffmpeg \
  && rm ffmpeg.tar.xz

# Set working directory to /var/task (default for Lambda)
WORKDIR /var/task

# Copy required files into the image
COPY .env ./
COPY package*.json ./
COPY tsconfig.json ./
COPY index.ts ./

RUN npm install
RUN npm run build

# Specify the Lambda handler (file.exportedFunction)
CMD ["index.handler"]
