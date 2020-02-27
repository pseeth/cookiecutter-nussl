import sys	
import os	

# If NUSSL_DIRECTORY is defined, then this will use the version of NUSSL that it points to.	
if os.getenv('NUSSL_DIRECTORY'):	
    sys.path.insert(0, os.getenv('NUSSL_DIRECTORY'))	

from . import algorithms	
from . import dataset	
from . import model	

import logging	

# Set up logging format here.	
logging.basicConfig(	
    format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',	
    datefmt='%Y-%m-%d:%H:%M:%S',	
    level=logging.INFO	
) 