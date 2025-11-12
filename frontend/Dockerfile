# === Stage 1: Build the React Application ===
FROM node:20-alpine as build

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json (or yarn.lock)
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application source code
COPY . .

# Build the application for production
RUN npm run build

# === Stage 2: Serve the application with Nginx ===
FROM nginx:1.25-alpine

# Copy the static build files from the 'build' stage
COPY --from=build /app/build /usr/share/nginx/html

# Nginx will automatically look for and serve the index.html file
# from the /usr/share/nginx/html directory.

# Expose port 80 for the Nginx server
EXPOSE 80

# The default Nginx command will start the server.
# This command keeps the container running in the foreground.
CMD ["nginx", "-g","daemon off;"]