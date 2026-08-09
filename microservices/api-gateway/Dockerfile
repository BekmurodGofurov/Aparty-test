# ── API Gateway Dockerfile ────────────────────────────────────────────────────
# nginx:alpine is ~25 MB — the smallest viable base for an Nginx container.

FROM nginx:alpine

# Remove the default nginx config to avoid conflicts
RUN rm /etc/nginx/conf.d/default.conf

# Copy our custom gateway config
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

# nginx starts in the foreground by default in the official image
CMD ["nginx", "-g", "daemon off;"]
