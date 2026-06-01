FROM ghcr.io/astral-sh/uv:latest AS uv_bin

FROM python:3.12-slim
WORKDIR /app

# 1. Install uv
COPY --from=uv_bin /uv /uvx /bin/

# 2. Setup environment
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PATH="/app/.venv/bin:$PATH"

# 3. Install dependencies (STAYS CACHED unless pyproject.toml changes)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# 4. Copy app code (Changes frequently)
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .

# 5. Create data dirs
RUN mkdir -p /app/data/uploads /app/data/evaluations

# Note: We are NOT copying the .onnx or .db files here 
# unless you explicitly add: COPY de_DE-thorsten-low.onnx .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]