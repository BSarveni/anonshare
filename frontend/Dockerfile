FROM node:20-alpine

WORKDIR /app

# Vite bakes env vars at build time — Railway passes service variables into the build.
ARG VITE_API_URL
ARG VITE_WS_URL
ARG VITE_CLOUDINARY_CLOUD_NAME
ARG VITE_CLOUDINARY_UPLOAD_PRESET
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_WS_URL=$VITE_WS_URL
ENV VITE_CLOUDINARY_CLOUD_NAME=$VITE_CLOUDINARY_CLOUD_NAME
ENV VITE_CLOUDINARY_UPLOAD_PRESET=$VITE_CLOUDINARY_UPLOAD_PRESET

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build
RUN npm install -g serve

EXPOSE 3000

# Railway injects PORT; default 3000 for local Docker.
CMD ["sh", "-c", "serve -s dist -l ${PORT:-3000}"]
