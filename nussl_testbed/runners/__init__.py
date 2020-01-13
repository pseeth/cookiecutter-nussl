"""
# Runners

All of your code is executed via one of the runners in this module. This
module also contains a number of utilities for loading and saving YAML files, 
and loading and saving experiment directories (with or without comet.ml).
"""

from comet_ml import BaseExperiment
BaseExperiment._report_summary = lambda args : None

from .docker_runner import DockerRunner