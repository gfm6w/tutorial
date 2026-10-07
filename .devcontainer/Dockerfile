FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

RUN rm -f /etc/apt/sources.list.d/yarn.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends curl unzip rsync \
    && rm -rf /var/lib/apt/lists/*

USER vscode
ENV VIRTUAL_ENV=/home/vscode/venv
ENV PATH=/home/vscode/venv/bin:$PATH

COPY --chown=vscode requirements.txt /tmp/requirements.txt
RUN python -m venv "$VIRTUAL_ENV" \
    && pip install --no-cache-dir -r /tmp/requirements.txt

RUN gridfm_datakit setup_pm

COPY --chown=vscode scripts/install_dynawo.sh /tmp/install_dynawo.sh
RUN bash /tmp/install_dynawo.sh

WORKDIR /workspace
EXPOSE 8888
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--notebook-dir=/workspace/notebooks"]
