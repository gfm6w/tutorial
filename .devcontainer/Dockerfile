# Layers go from the least to the most often changed. JULIA_CPU_TARGET is the
# target list of the official Julia binaries, so the precompiled PowerModels
# loads on any x86 host instead of compiling again on first use.
FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

RUN rm -f /etc/apt/sources.list.d/yarn.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends curl unzip rsync \
    && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.12.1 /uv /usr/local/bin/uv

USER vscode
ENV VIRTUAL_ENV=/home/vscode/venv
ENV PATH=/home/vscode/venv/bin:$PATH
ENV JULIA_CPU_TARGET="generic;sandybridge,-xsaveopt,clone_all;haswell,-rdrnd,base(1);x86-64-v4,-rdrnd,base(1)"

COPY --chown=vscode scripts/install_dynawo.sh /tmp/install_dynawo.sh
RUN bash /tmp/install_dynawo.sh

COPY --chown=vscode requirements.txt /tmp/requirements.txt
RUN uv venv --seed "$VIRTUAL_ENV" \
    && uv pip install --no-cache -r /tmp/requirements.txt

RUN gridfm_datakit setup_pm

COPY --chown=vscode . /workspace
WORKDIR /workspace
RUN python scripts/check_setup.py

EXPOSE 8888
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--notebook-dir=/workspace/notebooks"]
