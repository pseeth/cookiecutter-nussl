SHELL := /bin/bash
env_file = $(ENV_FILE)
gpus = ""
name = ""

install:
	poetry install

freeze_requirements:
	poetry export -f requirements.txt --without-hashes > requirements.txt

docker:
	make freeze_requirements
	source $(env_file) && \
	bash ./setup/build_docker_image.sh

check_environment:
	echo $(env_file)
	source $(env_file) && \
	printenv

check_container_environment:
	echo $(env_file)
	source $(env_file) && \
	poetry run python scripts/run_in_docker.py "printenv"

run_in_host:
	source $(env_file) && \
	CUDA_VISIBLE_DEVICES=$(gpus) poetry run $(command)

run_in_container:
	source $(env_file) && \
	CUDA_VISIBLE_DEVICES=$(gpus) NAME=$(name) poetry run python scripts/run_in_docker.py "$(command)"

pipeline:
	source $(env_file) && \
	poetry run python scripts/pipeline.py "${yml}"

jupyter:
	make command="jupyter lab" gpus=$(gpus) name=jupyter_lab run_in_container

test:
	echo "Running tests in host"
	make command="python -m pytest . -s" run_in_host
	echo "Running tests in container"
	make command="python -m pytest . -s" run_in_container