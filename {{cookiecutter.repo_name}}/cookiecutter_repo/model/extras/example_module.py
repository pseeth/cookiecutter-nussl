from torch import nn

class ExampleModule(nn.Module):
    """
    An example of a user-defined module that is passed to SeparationModel for building
    up the model. This should be imported explicitly in the init to be included.
    """
    def __init__(self):
        super(ExampleModule, self).__init__()
                
    def forward(self, data):
        return data
