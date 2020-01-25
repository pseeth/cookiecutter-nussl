from .. import dataset, model

def load_dataset(dataset_class, dataset_folder, dataset_config):
    """
    This is a helper function that looks in the 
    :py:mod:`src.dataset` module.
    
    Args:
        dataset_class (str): Name of the dataset class you want to
        instantiate (e.g. Scaper, MixSourceFolder).

        dataset_folder (str): Folder you want to load the data from.

        dataset_config (dict): Configuration of the dataset
    
    Returns:
        :py:class:`torch.utils.data.Dataset`: Instantiated DatasetClass given the parameters.
    """
    DatasetClass = getattr(dataset, dataset_class)
    dataset_instance = DatasetClass(dataset_folder, dataset_config)
    return dataset_instance

def load_model(model_config):
    """
    Loads a deep :py:class:`SeparationModel` given a model configuration.
    
    Args:
        model_config (dict): Model configuration with a 'class' key. The rest of the keys
        get put into the 'args'.
    
    Returns:
        :py:class:`SeparationModel`: Instantiated deep model given the parameters.
    """
    model_class = model_config.pop('class', 'SeparationModel')
    ModelClass = getattr(model, model_class)
    if model_class == 'SeparationModel':
        model_instance = ModelClass(model_config, extra_modules=model.extras)
    else:
        model_instance = ModelClass(model_config)
    return model_instance