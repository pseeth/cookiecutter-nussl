SHELL := /bin/bash
env_file = $(ENV_FILE)
gpus = 0
name = default

install:
	poetry self:update --preview
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
	poetry run $(command)

run_in_container:
	source $(env_file) && \
	poetry run python scripts/run_in_docker.py "$(command)" --gpus $(gpus) --name $(name)

jupyter:
	make command="jupyter lab" gpus=$(gpus) name=jupyter_lab run_in_container

test:
	echo "Running tests in host"
	make command="python -m pytest . -s" run_in_host
	echo "Running tests in container"
	make command="python -m pytest . -s" run_in_container