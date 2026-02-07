# Multi-stage build: Build React frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app

# Copy package files
COPY react_frontend/package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy frontend source
COPY react_frontend/ ./

# Build frontend
RUN npm run build

# Stage 2: Nginx server
FROM nginx:1.25-alpine

LABEL maintainer="RAG Team"
LABEL service="gateway"
LABEL version="2.0.0"

# Copy nginx configuration
COPY app/services/gateway/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built frontend from previous stage
COPY --from=frontend-builder /app/build /usr/share/nginx/html/

# Create log directory
RUN mkdir -p /var/log/nginx

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/health || exit 1

# Run nginx
CMD ["nginx", "-g", "daemon off;"]
