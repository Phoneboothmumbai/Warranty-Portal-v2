# Use Debian-slim (more stable than Alpine)
FROM node:20-slim

WORKDIR /app

# Fix OpenSSL issues
ENV NODE_OPTIONS=--openssl-legacy-provider

# Copy package files
COPY package.json package-lock.json* ./

# Install with npm (more reliable without lockfile)
RUN npm cache clean --force && \
    npm install --legacy-peer-deps --no-audit --no-fund

# Copy source
COPY . .

EXPOSE 3000
CMD ["npm", "start"]
