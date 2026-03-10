# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy only package.json (not lock file)
COPY package.json ./

# Install dependencies fresh for Alpine Linux
RUN npm install

# Copy source code
COPY . .

# Build argument for API URL
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

# Build the app
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy custom nginx config template
COPY nginx.conf /etc/nginx/templates/default.conf.template

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Railway uses dynamic PORT
ENV PORT=80
EXPOSE $PORT

# Use envsubst to replace ${PORT} in nginx config, then start nginx
CMD sh -c "envsubst '\$PORT' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"
