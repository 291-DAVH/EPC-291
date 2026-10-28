# API image. Build from the repository root:  docker build -f infra/docker/backend.Dockerfile -t epc-backend .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 EPC_REPO=/app
WORKDIR /app

# Engine packages and the data the backend reads (rules, schemas, templates, plugin manifests)
COPY engine ./engine
COPY shared ./shared
COPY management ./management
COPY claude ./claude
COPY backend ./backend
COPY database ./database
COPY tools ./tools

RUN pip install --no-cache-dir \
      -e engine/aea90364 -e engine/rules -e engine/standards -e engine/dxf -e engine/symbols -e engine/titleblock -e engine/plan -e engine/sld -e engine/mld -e engine/drawing -e engine/documents \
      -e "backend[analysis]" -r database/requirements.txt

RUN useradd --create-home epc && mkdir -p /data/projects && chown -R epc /data
USER epc
ENV EPC_PROJECTS=/data/projects EPC_ROLE=user EPC_ENV=production
VOLUME /data/projects
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/api/health')"
CMD ["uvicorn", "epc.main:app", "--host", "0.0.0.0", "--port", "8000"]
