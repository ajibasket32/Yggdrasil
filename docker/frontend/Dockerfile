ARG NODE_IMAGE=node:22.15.0-alpine
ARG NGINX_IMAGE=nginx:1.28.0-alpine

FROM ${NODE_IMAGE} AS build

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

FROM ${NGINX_IMAGE}

COPY docker/frontend/default.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80