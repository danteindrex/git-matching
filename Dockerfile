FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci

# Copy the rest of the application
COPY . .
ENV NODE_OPTIONS=--max-old-space-size=2048

# Build the application
RUN npm run build

# Start the application
CMD ["npm", "start"]
