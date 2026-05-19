# syntax=docker/dockerfile:1.7

FROM node:18-alpine as build

WORKDIR /app

COPY react_frontend/package*.json ./

RUN --mount=type=cache,target=/root/.npm \
    npm ci

COPY react_frontend/ ./

RUN npm run build

FROM nginx:alpine

COPY --from=build /app/build /usr/share/nginx/html

COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
