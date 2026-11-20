FROM node:24-alpine AS panel
WORKDIR /build
COPY package.json package-lock.json panel.tsx ./
RUN npm ci --no-audit --no-fund && npm run build

FROM python:3.12-slim
WORKDIR /srv
COPY requirements.txt requirements-dev.txt ./
ARG REQUIREMENTS=requirements.txt
RUN pip install --no-cache-dir -r "$REQUIREMENTS" && useradd -m eco
COPY app app
COPY --from=panel /build/app/static/panel.js app/static/panel.js
COPY migrations migrations
COPY alembic.ini ./
COPY datasets datasets
COPY tests tests
USER eco
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000","--no-access-log"]
