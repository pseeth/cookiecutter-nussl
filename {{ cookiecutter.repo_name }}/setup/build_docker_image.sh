#!/usr/bin/env bash
# [wf] build docker image
set -ex

docker --version
if [ $? -ne 0 ]; then
  echo "Cannot invoke docker command"
  exit 1
fi

if [[ -z "${DOCKER_IMAGE_NAME}" ]]; then
  echo "DOCKER_IMAGE_NAME environment variable is not set! Create, configure and run set_environment_local.sh using set_environment_default.sh as the template."
  exit 1
fi

if [ "${DOCKER_IMAGE_NAME}" == "pseeth/nussl:latest" ]; then
    echo "DOCKER_IMAGE_NAME is set to pseeth/nussl:latest...pulling container from docker.io"
    docker pull ${DOCKER_IMAGE_NAME}
else
  docker build \
      --build-arg user_id=$UID \
      --build-arg user_name=`whoami` \
      --build-arg jupyter_password_hash=$JUPYTER_PASSWORD_HASH \
      -t $DOCKER_IMAGE_NAME \
      -f Dockerfile .
fi

