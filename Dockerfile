# syntax=docker/dockerfile:1.4

########################
# Frontend Build Stage #
########################
FROM --platform=$BUILDPLATFORM node:18-alpine AS frontend-builder

WORKDIR /frontend
COPY frontend/ /frontend/

RUN if [ ! -d dist ]; then yarn install && yarn build; fi


#####################################
# Select correct Ultralytics base   #
#####################################
FROM scratch AS base

# AMD64 uses fixed Ultralytics CPU build
FROM ultralytics/ultralytics:8.3.96-cpu AS base-amd64

# ARM64 uses fixed Ultralytics ARM64 build
FROM ultralytics/ultralytics:8.3.234-arm64 AS base-arm64

# Dispatch to correct base image based on target architecture
FROM base-${TARGETARCH} AS runtime


####################################
# Final Runtime Stage
####################################
WORKDIR /docker-app

# Copy backend
COPY . .

# Install Python requirements
RUN pip install --no-cache-dir -r requirements_docker.txt \
    && rm -rf /root/.cache/pip

# Copy built frontend
COPY --from=frontend-builder /frontend/dist /docker-app/frontend/dist

EXPOSE 8070

CMD ["python", "run.py", "--setup"]
