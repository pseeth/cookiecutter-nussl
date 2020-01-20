from runners import DockerRunner
from runners.script_runner_pool import ScriptRunnerPool

def test_docker_runner():
    runner = DockerRunner()
    runner.run("ls", gpus='0')
    runner.container.wait()
    
    runner.run("ls", gpus='')