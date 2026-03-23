# Stage 1: Builder
FROM continuumio/miniconda3:24.11.1-0 AS builder
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake git pkg-config \
    libeigen3-dev libboost-all-dev liburdfdom-dev libassimp-dev \
    && rm -rf /var/lib/apt/lists/*
# Pinocchio ecosystem via conda-forge
RUN conda install -y -c conda-forge \
    python=3.11 numpy matplotlib \
    pinocchio crocoddyl \
    && conda clean --all --yes
RUN pip install --no-cache-dir \
    pin-pink qpsolvers osqp \
    pytest pytest-cov pytest-xdist pytest-timeout pytest-mock \
    ruff mypy hypothesis

# Stage 2: Runtime
FROM continuumio/miniconda3:24.11.1-0 AS runtime
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx libosmesa6 curl \
    && rm -rf /var/lib/apt/lists/*
ARG USER_NAME=athlete
ARG USER_ID=1000
ARG GROUP_ID=1000
RUN groupadd -g ${GROUP_ID} ${USER_NAME} && \
    useradd -m -u ${USER_ID} -g ${GROUP_ID} -s /bin/bash ${USER_NAME}
COPY --from=builder /opt/conda /opt/conda
ENV PYTHONPATH="/workspace/src"
ENV PATH="/opt/conda/bin:$PATH"
WORKDIR /workspace
COPY --chown=${USER_NAME}:${USER_NAME} src/ ./src/
COPY --chown=${USER_NAME}:${USER_NAME} tests/ ./tests/
COPY --chown=${USER_NAME}:${USER_NAME} pyproject.toml conftest.py ./
USER ${USER_NAME}
CMD ["/bin/bash"]

# Stage 3: Training
FROM runtime AS training
USER root
RUN pip install --no-cache-dir gymnasium>=0.29.0 stable-baselines3>=2.0.0
USER ${USER_NAME}
CMD ["/bin/bash"]
