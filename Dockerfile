# Set the base image
FROM continuumio/miniconda3:latest AS builder

# Ensure UTF-8 locale (C.UTF-8 is already set in base image, but we explicitly set it for clarity)
# C.UTF-8 is recommended by Python core developers and doesn't require locale files
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONIOENCODING=utf-8

# Install system dependencies
RUN apt-get update && \
    apt-get install -y sudo libusb-1.0 gcc g++ python3-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /home/hummingbot

# Create conda environment
COPY setup/environment.yml /tmp/environment.yml
RUN conda env create -f /tmp/environment.yml && \
    conda clean -afy && \
    rm /tmp/environment.yml

# Copy remaining files
COPY bin/ bin/
COPY hummingbot/ hummingbot/
COPY scripts/ scripts/
COPY controllers/ controllers/
COPY scripts/ scripts-copy/
COPY setup.py .
COPY LICENSE .
COPY README.md .

# activate hummingbot env when entering the CT
SHELL [ "/bin/bash", "-lc" ]
RUN echo "conda activate hummingbot" >> ~/.bashrc

COPY setup/pip_packages.txt /tmp/pip_packages.txt
RUN python3 -m pip install --no-deps eip712-structs && \
    python3 -m pip install lighter-sdk x10-python-trading fast-stark-crypto && \
    rm /tmp/pip_packages.txt


RUN python3 setup.py build_ext --inplace -j 8 && \
    rm -rf build/ && \
    find . -type f -name "*.cpp" -delete


# Build final image using artifacts from builder
FROM continuumio/miniconda3:latest AS release

# Dockerfile author / maintainer
LABEL maintainer="Fede Cardoso @dardonacci <federico@hummingbot.org>"

# Build arguments
ARG BRANCH=""
ARG COMMIT=""
ARG BUILD_DATE=""
LABEL branch=${BRANCH}
LABEL commit=${COMMIT}
LABEL date=${BUILD_DATE}

# Ensure UTF-8 locale (C.UTF-8 is already set in base image, but we explicitly set it for clarity)
# C.UTF-8 is recommended by Python core developers and doesn't require locale files
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONIOENCODING=utf-8

# Set ENV variables
ENV COMMIT_SHA=${COMMIT}
ENV COMMIT_BRANCH=${BRANCH}
ENV BUILD_DATE=${BUILD_DATE}

ENV INSTALLATION_TYPE=docker

# Install system dependencies
RUN apt-get update && \
    apt-get install -y sudo libusb-1.0 && \
    rm -rf /var/lib/apt/lists/*

# Create mount points
RUN mkdir -p /home/hummingbot/conf /home/hummingbot/conf/connectors /home/hummingbot/conf/strategies /home/hummingbot/conf/controllers /home/hummingbot/conf/scripts /home/hummingbot/logs /home/hummingbot/data /home/hummingbot/certs /home/hummingbot/scripts /home/hummingbot/controllers

WORKDIR /home/hummingbot

# Copy all build artifacts from builder image
COPY --from=builder /opt/conda/ /opt/conda/
COPY --from=builder /home/ /home/

# Setting bash as default shell because we have .bashrc with customized PATH (setting SHELL affects RUN, CMD and ENTRYPOINT, but not manual commands e.g. `docker run image COMMAND`!)
SHELL [ "/bin/bash", "-lc" ]

# Set the default command to run when starting the container

CMD conda activate hummingbot && ./bin/hummingbot_quickstart.py 2>> ./logs/errors.log
