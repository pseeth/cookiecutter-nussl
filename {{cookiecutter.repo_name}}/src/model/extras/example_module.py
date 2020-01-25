from torch import nn

class ExampleModule(nn.Module):
    """
    An example of a user-defined module that is passed to SeparationModel for building
    up the model. This should be imported explicitly in the init to be included.

    Now that it's defined here, it can be used in your model configuration like so:

    .. code-block:: yaml

       model_config:
        class: SeparationModel
        modules:
            log_spectrogram
            example_module:
              class: ExampleModule
              args:
        connections:
            - !!python/tuple      # tuple containing two things:
              - example_module    # unique name given to module above
              - [log_spectrogram] # list of runtime arguments needed by that module 
                                # (e.g. output of prev layer)
        output:
        - example_module

    """
    def __init__(self):
        super(ExampleModule, self).__init__()
                
    def forward(self, data):
        return data