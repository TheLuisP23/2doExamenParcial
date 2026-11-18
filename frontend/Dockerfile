# REQ-P-001 — runtime no-root (nginx-unprivileged, UID 101). El bundle `dist/` se construye antes
# con `npm ci && npm run build` (local o CI) para no depender de npm dentro del build de Docker.
FROM nginxinc/nginx-unprivileged:1.27-alpine
COPY nginx/templates /etc/nginx/templates
COPY dist /usr/share/nginx/html
USER 101
EXPOSE 8080
