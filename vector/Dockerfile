##########################
# --- Stage 1: Builder ---
##########################
FROM python:3.12-slim-bookworm AS builder

ENV DEBIAN_FRONTEND=noninteractive
ENV ACCEPT_EULA=Y

WORKDIR /app

# Copy requirements for caching
COPY requirements.txt /app/

# Install system dependencies for building the DB
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    make \
    libreadline-dev \
    sqlite3 \
    libsqlite3-dev \
    python3-dev \
    python3-setuptools \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
RUN pip install -r /app/requirements.txt

# Copy application files
COPY . /app

# Ensure permissions
RUN chmod -R 755 /app

# Build the SQLite database

WORKDIR /app/mimiciv

RUN rm -f /app/mimiciv/mimiciv.db && sync && python3 /app/mimiciv/import.py

RUN sqlite3 /app/mimiciv/mimiciv.db < /app/mimiciv/mimiciv_add_patient_info.sql

# Validate DB exists!
RUN test -f mimiciv.db || (echo "mimiciv.db was not created!" && exit 1)

RUN ls -l /app/mimiciv/ && sleep 2

WORKDIR /app

# RUN python -m spacy download en_core_web_trf


############################
# --- Stage 2: Runtime ---
############################
FROM python:3.12-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive
ENV ACCEPT_EULA=Y
ENV PIP_DEFAULT_TIMEOUT=180

WORKDIR /app



# Install runtime-only system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    curl \
    iputils-ping \
    procps \
    man-db \
    gnupg2 \
    apt-transport-https \
    unixodbc \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from the builder stage
COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy just the final application and built DB
COPY --from=builder /app/mimiciv/mimiciv.db /app/mimiciv/mimiciv.db
COPY --from=builder /app /app


# Optional: force permissions again
RUN chmod -R 755 /app

# Expose ports
EXPOSE 8000 5678

RUN python -m spacy download "en_core_web_trf"


# Start debugger + app
ENTRYPOINT ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
