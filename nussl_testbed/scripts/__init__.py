"""
# Scripts

All of the code you write should always be run via a script. Scripts in this
project take a special form for the purposes of reproducibility. Scripts always
taken in a YAML file which contains all the information needed to run the 
script. For example, `scripts/resample.py` takes in YAML file as follows:

```
.. include:: ../data_prep/musdb/resample.yml
```

This YAML File is processed by the script to resample two datasets. A special 
key called `jobs` can be used to run the script multiple times (once for each job).
The file above contains two jobs, one which resamples the train data and the other
which resamples the test data.

You must write a corresponding YAML file for each script that you write and execute.
This is to reduce dependence on "magic terminal commands" that become undocumented and
unmentioned as project complexity grows. Finally, reproducing an experiment then just 
becomes executing a sequence of YAML files.

The scripts here contain  
"""

from .pipeline import main