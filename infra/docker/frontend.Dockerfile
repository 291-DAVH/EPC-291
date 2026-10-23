# Static front (customer app on :8080, console on :8081) behind nginx, which proxies /api to the backend.
# Build from the repository root:  docker build -f infra/docker/frontend.Dockerfile -t epc-frontend .
FROM node:20-alpine AS build
WORKDIR /src
COPY frontend/package.json frontend/package-lock.json frontend/tsconfig.base.json ./
COPY frontend/packages ./packages
COPY frontend/web ./web
COPY frontend/console ./console
RUN npm ci && npm run build

FROM nginx:1.27-alpine
COPY infra/docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /src/web/dist /usr/share/nginx/html/web
COPY --from=build /src/console/dist /usr/share/nginx/html/console
EXPOSE 8080 8081
