# MossRouter MCP — Phase 2b
FROM node:20-alpine

WORKDIR /app

# Copy package files first for better layer caching
COPY package*.json ./
RUN npm ci --production

# Copy source
COPY . .

# Expose default port
EXPOSE 4023

# Default to mock for safety; override in prod compose / env
ENV MOSS_MOCK=1
ENV SKIP_PAYMENT=1

CMD ["node", "server.js"]
