# Production-ready Dockerfile for React frontend
# Using Node 18 LTS for maximum compatibility with react-scripts 5.x
FROM node:18-bookworm-slim

WORKDIR /app

# Install essential build tools and clean up in same layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    make \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for stable builds
ENV NODE_OPTIONS=--openssl-legacy-provider
ENV SKIP_PREFLIGHT_CHECK=true
ENV GENERATE_SOURCEMAP=false
ENV CI=false

# Copy package files first (better layer caching)
COPY package.json ./

# Install yarn globally and use it (as specified in packageManager)
RUN npm install -g yarn@1.22.22 && \
    yarn install --network-timeout 600000 --ignore-engines

# Copy rest of the source code
COPY . .

EXPOSE 3000

# Use yarn to run start script (which calls craco start)
CMD ["yarn", "start"]
