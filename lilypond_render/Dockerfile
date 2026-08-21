FROM python:3.14-slim

# extracted from lilypond binary
RUN apt-get install -y --no-install-recommends \
    git \
    openssh-client \
    build-essential \
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
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /usr/local/share/fonts/custom-fonts/
COPY ./lilypond_render/fonts/* /usr/local/share/fonts/custom-fonts/
RUN fc-cache -fv

# git + openssh-client: this service `git pull`s over ssh at runtime
# build-essential: covers anything in uv.lock that needs to compile
# NOTE: lilypond itself is NOT installed here -- it's bind-mounted in from
# the host at runtime (see docker-compose.yml), since it's a static release
# already installed on the host at /usr/local/lilypond.
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    openssh-client \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

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
