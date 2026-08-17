FROM python:3.12.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --system runtime \
    && useradd --system --gid runtime --home-dir /app runtime

WORKDIR /app

COPY --chown=runtime:runtime main/retrieval-runtime/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --requirement /app/requirements.txt

COPY --chown=runtime:runtime main/retrieval-runtime/retrieval_runtime /app/retrieval_runtime
RUN chmod -R a=rX /app

USER runtime

EXPOSE 8090

HEALTHCHECK --interval=20s --timeout=3s --retries=3 \
  CMD ["python", "-c", "import urllib.request; assert urllib.request.urlopen('http://127.0.0.1:8090/healthz', timeout=2).status == 200"]

CMD ["uvicorn", "retrieval_runtime.main:app", "--host", "0.0.0.0", "--port", "8090", "--no-access-log"]
