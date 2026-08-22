FROM python:3.14-slim

# extracted from lilypond binary
# then some git/ssh stuff, then gs (required by ly)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    guile-3.0-libs \
    libgc1 \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libfontconfig1 \
    libfreetype6 \
    libcairo2 \
    libpng16-16 \
    libharfbuzz0b \
    libfribidi0 \
    libthai0 \
    libexpat1 \
    libbrotli1 \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxcb1 \
    libxcb-render0 \
    libxcb-shm0 \
    libpixman-1-0 \
    libmount1 \
    libselinux1 \
    libgraphite2-3 \
    libdatrie1 \
    libxau6 \
    libxdmcp6 \
    libunistring5 \
    libgmp10 \
    git \
    openssh-client \
    build-essential \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /usr/local/share/fonts/custom-fonts/
COPY ./lilypond_render/fonts/* /usr/local/share/fonts/custom-fonts/
RUN fc-cache -fv

RUN git config --global --add safe.directory /app/lilypond_render/raw-template

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# lockfile is shared across all services at the repo root
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY . .
RUN uv sync --frozen

ENV PATH="/app/.venv/bin:/usr/local/bin:${PATH}"

RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh
RUN ssh-keyscan github.com gitlab.com >> /root/.ssh/known_hosts 2>/dev/null || true

WORKDIR /app/lilypond_render

CMD ["uv", "run", "python", "render.py", "--docker"]
