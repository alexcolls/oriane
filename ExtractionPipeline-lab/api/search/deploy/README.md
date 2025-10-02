# Oriane Search API – Build and Deploy Scripts

This folder contains helper scripts that build and push Docker images for the Oriane API to Amazon Elastic Container Registry (ECR).

Scripts available:

1. `deploy_to_ecr.sh` – a lightweight script suited for quick, one-off pushes.
2. `push_image.sh` – a more comprehensive script that adds GPU-focused build flags, multiple tags, and additional safety checks.

---

## 1. Prerequisites

Before running either script make sure that:

- Docker is installed and the daemon is running.
- The AWS CLI v2 is installed and configured with an identity that has **ECR** permissions (`ecr:GetAuthorizationToken`, `ecr:*Repository*`, `ecr:PutImage`, etc.).
  Use `aws configure` or export `AWS_PROFILE` / `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_SESSION_TOKEN`.
- Git is available in your `PATH` – commit information is embedded as Docker labels.
- For **GPU builds** (`push_image.sh`) you are on a host with NVIDIA® drivers and the `nvidia-docker` runtime (or a compatible CUDA-capable environment).

---

## 2. Common Environment Variables

Both scripts expose variables that can be **overridden at runtime** to suit different environments. Simply prefix the script call with the values you want to change:

| Variable          | Default                                         | Description                                               |
| ----------------- | ----------------------------------------------- | --------------------------------------------------------- |
| `ACCOUNT_ID`      | `509399609859`                                  | AWS account that owns the ECR registry                    |
| `AWS_REGION`      | `us-east-1`                                     | AWS region to push to                                     |
| `IMAGE_NAME`      | _(see script)_                                  | Logical image name (repository)                           |
| `REPOSITORY_NAME` | `oriane-search-api-v1-dev` _(deploy_to_ecr.sh)_ | ECR repository; created automatically if it doesn't exist |
| `IMAGE_TAG`       | `1.0.0` _(deploy_to_ecr.sh)_                    | Explicit tag to apply in addition to `latest`             |
| `VERSION`         | `1.2.0` _(push_image.sh)_                       | Semantic version to tag                                   |

Example of overriding several values:

```bash
AWS_REGION=eu-central-1 \
ACCOUNT_ID=123456789012 \
IMAGE_TAG=2.0.0 \
REPOSITORY_NAME=oriane-api-prod \
./deploy_to_ecr.sh
```

---

## 3. `deploy_to_ecr.sh` – Quick Push

The script:

1. Builds the Docker image defined in `../Dockerfile`.
2. Logs in to ECR using the AWS CLI.
3. Creates the ECR repository if necessary.
4. Tags the image as `<IMAGE_TAG>` **and** `latest`.
5. Pushes both tags to ECR.

Run it from the `api/deploy` directory:

```bash
chmod +x deploy_to_ecr.sh   # once
./deploy_to_ecr.sh
```

You should see output similar to:

```
🚀 Deploying Oriane API to ECR
Registry: 509399609859.dkr.ecr.us-east-1.amazonaws.com/oriane-search-api-v1
Repository: oriane-search-api-v1-dev
Tag: 1.0.0
…
🎉 Deployment Complete!
```

---

## 4. `push_image.sh` – Full Featured GPU-Ready Push

In addition to what `deploy_to_ecr.sh` does, this script:

- Embeds build metadata (`BUILD_DATE`, `GIT_COMMIT`, `GIT_BRANCH`).
- Builds with `--platform linux/amd64` and GPU-ready Dockerfile arguments.
- Saves the image to a `.tar`, reloads it, and then pushes **three** tags: `latest`, `${VERSION}`, and the short Git SHA.
- Implements timeouts and colourised logs.

Invoke it the same way:

```bash
chmod +x push_image.sh   # once
./push_image.sh
```

Override defaults if needed:

```bash
VERSION=2.0.1 IMAGE_NAME=oriane-api-gpu ./push_image.sh
```

---

## 5. Troubleshooting & Tips

- **Authentication errors** – ensure your AWS credentials are valid and that your IAM user/role can access ECR in the chosen region.
- **Docker build failures** – run `docker build` manually with the same arguments printed by the script to debug.
- **Large image pushes** – a slow connection may require increasing the timeout in `push_image.sh` (`timeout 3000` → seconds).
- **Permissions** – scripts use `set -e`; any failure will stop execution. Read the log lines above the error for clues.

---

## 6. After the Push

The image URIs printed at the end can be referenced in:

- AWS ECS task definitions.
- EKS / Kubernetes deployments.
- Docker Compose files (after an `aws ecr get-login-password` on the target host).

Happy shipping! 🚀
