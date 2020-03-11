# 1. Download ChemAxon Marvin for Debian from https://chemaxon.com/ and save to ./Dockerfile_assets/marvin_linux.deb
# 2. Obtain license for Marvin and save to ./Dockerfile_assets/chemaxon.license.cxl
# 3. Build with `docker build -f Dockerfile Dockerfile_assets --tag karrlab/obj_tables:latest`

# Start from Ubuntu (e.g., bionic - 18.04.4)
FROM ubuntu

# Set default language to UTF-8 US English
RUN apt-get update -y \
    && apt-get install --no-install-recommends -y \
        locales \
    && rm -rf /var/lib/apt/lists/* \
    && locale-gen en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

# Install Git
RUN apt-get update -y \
    && apt-get install --no-install-recommends -y \
        git \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Install Python (e.g., 3.6.9), pip, and setuptools
RUN apt-get update -y \
    && apt-get install --no-install-recommends -y \
        python3 \
        python3-pip \
    && pip3 install -U pip setuptools \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Install Open Babel 2.4.1
ARG openbabel_version=2.4.1
RUN apt-get update -y \
    && apt-get install --no-install-recommends -y \
        build-essential \
        cmake \
        libcairo2-dev \
        libeigen3-dev \
        libxml2 \
        libxml2-dev \
        tar \
        wget \
        zlib1g-dev \
    \
    && cd /tmp \
    && openbabel_version_dash=$(echo $openbabel_version | sed 's/\./-/g') \
    && wget https://github.com/openbabel/openbabel/archive/openbabel-${openbabel_version_dash}.tar.gz -O /tmp/openbabel-${openbabel_version}.tar.gz \
    && tar -xvvf /tmp/openbabel-${openbabel_version}.tar.gz \
    && cd openbabel-openbabel-${openbabel_version_dash} \
    && mkdir build \
    && cd build \
    && cmake .. \
    && make \
    # && make test \
    && make install \
    && ldconfig \
    && cd / \
    && rm -r /tmp/openbabel-${openbabel_version}.tar.gz \
    && rm -r /tmp/openbabel-openbabel-${openbabel_version_dash} \
    \
    && apt-get remove -y \
        build-essential \
        cmake \
        libcairo2-dev \
        libeigen3-dev \
        libxml2-dev \
        wget \
        zlib1g-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Install Open Babel Python interface
RUN apt-get update -y \
    && apt-get install --no-install-recommends -y \
        build-essential \
        libpython3-dev \
        swig \
    \
    && pip3 install openbabel \
    \
    && apt-get remove -y \
          build-essential \
          libpython3-dev \
          swig \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Install ChemAxon Marvin (e.g., 20.6)
COPY ./marvin_linux.deb /tmp/
COPY ./chemaxon.license.cxl /tmp/
RUN apt-get update -y \
    && apt-get install --no-install-recommends -y \
        default-jdk \
        default-jre \
    \
    && mkdir ~/.chemaxon \
    && mv /tmp/chemaxon.license.cxl ~/.chemaxon/license.cxl \
    && dpkg -i /tmp/marvin_linux.deb \
    \
    && rm /tmp/marvin_linux.deb \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*
ENV JAVA_HOME=/usr/lib/jvm/default-java \
    CLASSPATH=${CLASSPATH}:/opt/chemaxon/marvinsuite/lib/MarvinBeans.jar

# Install GraphViz
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends \
        graphviz \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Install ObjTables
RUN pip3 install \
    obj_tables[all]

# Test installations of ObjTables
ARG test=1
RUN if [ "$test" = "1" ]; then \
      apt-get update -y \
      && apt-get install --no-install-recommends -y \
          build-essential \
          libpython3-dev \
      \
      && cd / \
      && git clone https://github.com/KarrLab/obj_tables.git \
      && cd /obj_tables \
      && pip3 install pytest \
      && pip3 install -r tests/requirements.txt \      
      && python3 -m pytest tests/ \
      \
      && cd / \
      && rm -r obj_tables \
      && apt-get remove -y \
          build-essential \
          libpython3-dev \
      && apt-get autoremove -y \
      && rm -rf /var/lib/apt/lists/*; \
    fi
