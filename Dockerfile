FROM node:22-alpine

# Create app directory
WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install --production

# Copy the bridge script
COPY firewalla-mqtt-bridge.mjs ./

# Create credentials directory
RUN mkdir -p /app/credentials

# Create a non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Set permissions
RUN chown -R appuser:appgroup /app

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD node -e "const mqtt = require('mqtt'); const c = mqtt.connect('tcp://localhost:1883'); c.on('connect', () => { console.log('MQTT OK'); c.end(); process.exit(0); }); c.on('error', () => process.exit(1));"

# Run the bridge
CMD ["node", "firewalla-mqtt-bridge.mjs"]
