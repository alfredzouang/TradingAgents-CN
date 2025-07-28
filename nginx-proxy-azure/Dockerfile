# Use the official Nginx image as the base
FROM nginx:stable-alpine

# Remove the default nginx.conf
RUN rm /etc/nginx/nginx.conf

# Copy our custom nginx.conf
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port 80
EXPOSE 80

# Start Nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]
