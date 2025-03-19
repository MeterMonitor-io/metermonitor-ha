# Separate build stage for frontend using a Node container
FROM node:18-alpine as frontend-builder

WORKDIR /frontend
COPY frontend /frontend

# Install dependencies and build frontend
RUN yarn install && yarn build

# Final image to keep it minimal
FROM python:3.11.11-slim

WORKDIR /docker-app

# Copy backend files
COPY . /docker-app

# Install Python dependencies in the final container
RUN pip install ultralytics==8.3.93 --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# Copy the built frontend
COPY --from=frontend-builder /frontend/dist /docker-app/frontend/dist

# Expose the application port
EXPOSE 8070

# Command to run the application
CMD ["python", "run.py", "--setup"]
