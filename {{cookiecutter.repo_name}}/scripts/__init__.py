from argparse import ArgumentParser
from runners.utils import load_yaml
import inspect
import textwrap

def build_parser_for_yml_script():
    """
    Builds an ArgumentParser with a common setup. Used in the scripts.
    """
    parser = ArgumentParser()
    parser.add_argument(
        '-y',
        '--yml', 
        type=str, 
        help= """
            Path to .yml file containing command line arguments for the script. If the only key
            is 'jobs', then we assume it points to a list of jobs with parameters
            input_path and output_path. Each job is executed one after the other. The
            structure of each .yml file is up to you. If this is given, all other arguments
            to the script are not required (as they should be defined solely within the
            .yml).
            """
    )
    return parser

def sequential_job_execution(script_func, jobs):
    """
    Execute jobs one by one with a simple for loop.
    
    Args:
        script_func (function): Function to run.
        jobs (list): List of dictionaries containing arguments for function.
    """
    for args in jobs:
        script_func(**args)

def document_parser(script_name, reference):
    """
    Fancy function for documenting a parser easily. Runs the function to build
    the parser, then gets the parsers help texts and formats it into the
    function's doc string for sphinx. A bit hacky but works great!

    Args:
        script_name (str): Name of the script.
        reference (str): Where to point the reference function for the script 
            (e.g. the script that it runs).
    """
    def decorator(parser_func):
        parser = parser_func()
        help_text = parser.format_help()
        help_text = help_text.replace('sphinx-build', f'python -m scripts.{script_name} ')
        help_text = textwrap.indent(help_text, '\t\t  ')
        help_text = '   .. code-block:: none\n\n' + help_text

        doc = (
            f"""
            Builds the parser for :py:mod:`scripts.{script_name}`.
            
            {help_text}

            Also see the arguments to :py:func:`{reference}`.

            Returns:
                :class:`argparse.ArgumentParser`: The parser for this script.
            """
        )

        parser_func.__doc__ = doc        
        return parser_func
    return decorator
    

def cmd(script_func, parser_func, exec_func=sequential_job_execution):
    """
    Builds a parser for any script in the scripts/ directory. Scripts should have two
    main functions: 1) a function that actually runs the script and 2) a build_parser
    function that builds up an ArgumentParser with informative help text for the script.
    This function allows the command line arguments to be passed to the script either
    through the command line as normal or through a YAML file which has matching keyword
    arguments for the script. Positional arguments are discouraged.

    The arguments in the YAML file are checked by passing them back into the command 
    line parser function before giving them to the script. This also allows for default
    values to be defined in the script argument parser.

    A script can be called multiple times using a YAML file by having a top-level key
    called 'jobs'. 'jobs' should contain a list where each item in the list is a 
    set of arguments to be passed to the script one by one.

    For each script, simply add this like so::

        if __name__ == "__main__":
            cmd(script_func, parser_func)

    Then to run a script, simply do::

        python -m scripts.[script_name] --yml [path_to_yml_file] # for yml
        python -m scripts.[script_name] [--arg val] # for cmd line


    Arguments:
        script_func (function): A function that will take in the arguments as keyword
            arguments and perform some action.
        parser_func (function): A function that will build up the argument parser for
            the script.
    """
    jobs = []

    yml_parser = build_parser_for_yml_script()
    cmd_parser = parser_func()
    args = vars(yml_parser.parse_known_args()[0])
    extra_args = {}

    if args['yml'] is None:   
        args = vars(cmd_parser.parse_known_args()[0])
        jobs.append(args)
    else:
        _args = load_yaml(args['yml'])
        _jobs = []

        if 'jobs' in _args:
            _jobs = _args.pop('jobs')
            extra_args = _args
        else:
            _jobs.append(_args)
        
        for job in _jobs:
            if cmd_parser:
                args = []
                for key, val in job.items():
                    if isinstance(val, bool):
                        if val:
                            args.append(f'--{key}')
                    else:
                        args.append(f'--{key}')
                        args.append(str(val))
                args, unknown_args = cmd_parser.parse_known_args(args)
                args = vars(args)
                [job.pop(k) for k in args if k in job]
                args.update(job)
            else:
                args = job
            jobs.append(args)
    
    exec_args = inspect.getfullargspec(exec_func)[0]
    for key in extra_args.copy():
        if key not in exec_args:
            extra_args.pop(key)

    exec_func(script_func, jobs, **extra_args)