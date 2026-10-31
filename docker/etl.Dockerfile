FROM python:3.12-slim-bookworm

RUN apt-get update && \
    apt-get install -y --no-install-recommends openjdk-17-jre-headless ca-certificates && \
    rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PYSPARK_PYTHON=/usr/local/bin/python
ENV PYSPARK_DRIVER_PYTHON=/usr/local/bin/python
ENV PYTHONPATH=/workspace

WORKDIR /workspace

COPY requirements-etl.txt /tmp/requirements-etl.txt
ARG PIP_INDEX_URL=https://pypi.org/simple
RUN python -m pip install --no-cache-dir --index-url "$PIP_INDEX_URL" \
    -r /tmp/requirements-etl.txt

CMD ["python", "-m", "src.etl", "--month", "2024-01"]
