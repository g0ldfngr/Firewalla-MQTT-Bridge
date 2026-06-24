FROM node:22-alpine

WORKDIR /app

COPY package.json ./

RUN npm install --production

COPY firewalla-mqtt-bridge.mjs ./

RUN mkdir -p /app/credentials \
 && addgroup -S appgroup \
 && adduser -S appuser -G appgroup \
 && chown -R appuser:appgroup /app

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD node -e "import('fs').then(fs => { fs.accessSync('/app/credentials/fwgroup.json'); process.exit(0); }).catch(() => process.exit(1));"

CMD ["node", "firewalla-mqtt-bridge.mjs"]
