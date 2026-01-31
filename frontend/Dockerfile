# Production-grade Dockerfile using Debian (no Alpine SSL issues)
FROM node:20-slim

WORKDIR /app

# Install yarn globally (more reliable than npm)
RUN corepack enable && corepack prepare yarn@stable --activate

# Copy package files
COPY package.json yarn.lock* ./

# Install dependencies with yarn (faster, more reliable)
RUN yarn install --frozen-lockfile --network-timeout 600000 || yarn install --network-timeout 600000

# Copy source code
COPY . .

# Expose port
EXPOSE 3000

# Start the app
CMD ["yarn", "start"]
