import numpy as np
import random
import torch

def seed(s=0):
    ### Seeding
    torch.backends.cudnn.benchmark = True
    torch.manual_seed(s)
    torch.cuda.manual_seed(s)
    np.random.seed(s)
    random.seed(s)