import numpy as np
import random
import torch

def seed(s=0):
    """Seeds every possible random number generator
    with a specific seed to guarantee the same
    results with the same seed (hopefully). Currently
    supported RNGs are::

        torch.manual_seed
        torch.cuda.manual_seed
        np.random.seed
        random.seed

    If you use RNGs outside of this list in your project,
    then there's no guarantee of reproducibility.
    
    Args:
        s (int, optional): Seed to use. Defaults to 0.
    """
    torch.backends.cudnn.benchmark = True
    torch.manual_seed(s)
    torch.cuda.manual_seed(s)
    np.random.seed(s)
    random.seed(s)