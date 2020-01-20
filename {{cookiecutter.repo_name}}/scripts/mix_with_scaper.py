from src.dataset import scaper_mix
from . import cmd
from multiprocessing import cpu_count
import inspect

def mix_with_scaper(**kwargs):
    """
    Takes in keyword arguments containing the specification for mixing with Scaper. See
    :py:func:`src.dataset.scaper_mix` for a description of what should be in the
    kwargs. This function does some sanitation of the keyword arguments before 
    passing it to :py:func:`src.dataset.scaper_mix`.
    
    Args:
        kwargs (dict): All of the keyword arguments required for 
            :py:func:`src.dataset.scaper_mix`.
    """
    args = inspect.getfullargspec(scaper_mix)[0]
    keys_to_pop = []
    for key in kwargs.copy():
        if key not in args:
            kwargs.pop(key)

    if 'num_workers' in kwargs:      
        kwargs['num_workers'] = min(kwargs['num_workers'], cpu_count())
        
    scaper_mix(**kwargs)

if __name__ == '__main__':
    cmd(mix_with_scaper, lambda: None)