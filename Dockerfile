# Separate build stage for frontend using a Node container
FROM node:18-alpine AS frontend-builder

WORKDIR /frontend
COPY frontend /frontend

# Check if dist/ exists, if not, install deps and build
RUN if [ ! -d dist ]; then yarn install && yarn build; else echo "Skipping frontend build, dist/ already exists."; fi

# Final image to keep it minimal
FROM ultralytics/ultralytics:latest-cpu

WORKDIR /docker-app

# Copy backend files
COPY . /docker-app

# Install Python dependencies in the final container
RUN pip install --no-cache-dir -r requirements_docker.txt && rm -rf /usr/local/cuda/ && rm -rf /usr/local/nvidia/ && rm -rf /root/.cache/pip

# Copy the built frontend
COPY --from=frontend-builder /frontend/dist /docker-app/frontend/dist

# Expose the application port
EXPOSE 8070

# Command to run the application
CMD ["python", "run.py", "--setup"]
