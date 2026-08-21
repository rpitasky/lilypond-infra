FROM python:3.14-slim

# git + openssh-client: this service `git pull`s over ssh at runtime
# build-essential: covers anything in uv.lock that needs to compile
# NOTE: lilypond itself is NOT installed here -- it's bind-mounted in from
# the host at runtime (see docker-compose.yml), since it's a static release
# already installed on the host at /usr/local/lilypond.
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    openssh-client \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \

# 1. Install official LilyPond to auto-resolve all runtime dependencies
# 2. Purge only the official package binary, keeping all shared libraries
RUN apt-get update && \ apt-get install -y --no-install-recommends lilypond && \
    dpkg --purge --force-depends lilypond && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* \

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
