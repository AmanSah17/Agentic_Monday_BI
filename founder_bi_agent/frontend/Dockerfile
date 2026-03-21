# Stage 1: Build the Vite payload into static optimized files
FROM node:18-alpine AS builder

WORKDIR /app

# Listen to the exact Backend URL injected natively by render.yaml cross-communication
ARG VITE_BACKEND_URL
ENV VITE_BACKEND_URL=$VITE_BACKEND_URL

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# Stage 2: Serve securely behind Nginx
FROM nginx:alpine

# Flush out the default index pages and overwrite strict URL routing overrides
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Strip the optimized payload cleanly into the container bounds
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
