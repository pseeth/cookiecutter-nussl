FROM nvidia/cuda

ARG user_id
ARG user_name
ARG jupyter_password_hash
RUN groupadd -r $user_name && useradd -r -u $user_id -g $user_name $user_name
RUN chown $user_name /home

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV PATH /opt/conda/bin:$PATH

RUN apt-get update --fix-missing && apt-get install -y wget bzip2 ca-certificates \
    libglib2.0-0 libxext6 libsm6 libxrender1 \
    git mercurial subversion

RUN wget https://repo.anaconda.com/archive/Anaconda3-2019.03-Linux-x86_64.sh -O ~/anaconda.sh && \
    /bin/bash ~/anaconda.sh -b -p /opt/conda && \
    rm ~/anaconda.sh && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc && \
    echo "conda activate base" >> ~/.bashrc

RUN apt-get install -y curl grep sed dpkg && \
    TINI_VERSION=`curl https://github.com/krallin/tini/releases/latest | grep -o "/v.*\"" | sed 's:^..\(.*\).$:\1:'` && \
    curl -L "https://github.com/krallin/tini/releases/download/v${TINI_VERSION}/tini_${TINI_VERSION}.deb" > tini.deb && \
    dpkg -i tini.deb && \
    rm tini.deb && \
    apt-get clean

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && \
    apt-get -y install gcc mono-mcs && \
    rm -rf /var/lib/apt/lists/*

RUN conda install -c conda-forge widgetsnbextension
RUN conda install -c conda-forge nodejs
RUN conda install -c conda-forge sox
RUN apt-get update && apt-get install -y ffmpeg
RUN npm install --save-dev webpack

RUN conda install -c conda-forge pysoundfile
RUN apt-get update && \
    apt-get install libgl1-mesa-glx -y
RUN apt-get install groff -y
RUN apt-get install -y -qq less

ADD frozen_requirements.txt /
RUN pip install --ignore-installed -r /frozen_requirements.txt

COPY setup/melodia/ /usr/local/lib/vamp

RUN jupyter nbextension enable --py widgetsnbextension

USER $user_name 
ENV JUPYTER_PASSWORD $jupyter_password_hash
# Obtain the SHA hash for your chosen password and copy it above. To do this, use:
# from notebook.auth import passwd
# passwd()
# You'll be asked to put in your password twice. The SHA value will display.
# Copy it (without the single quotes) and paste it above. This will be the password you use to login to
# the Jupyter server.
RUN jupyter notebook --generate-config
RUN echo "c.NotebookApp.password='${JUPYTER_PASSWORD}'" >> /home/$user_name/.jupyter/jupyter_notebook_config.py

USER root