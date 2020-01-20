from .. import dataset, model

def load_dataset(dataset_class, dataset_folder, dataset_config):
    """
    This is a helper function that looks in the 
    ::py:mod:`src.dataset` module.
    
    Args:
        dataset_class (str): Name of the dataset class you want to
        instantiate (e.g. Scaper, MixSourceFolder).

        dataset_folder (str): Folder you want to load the data from.

        dataset_config (dict): Configuration of the dataset
    
    Returns:
        DatasetClass: Instantiated DatasetClass given the parameters.
    """
    DatasetClass = getattr(dataset, dataset_class)
    dataset_instance = DatasetClass(dataset_folder, dataset_config)
    return dataset_instance

def load_model(model_config):
    """
    [summary]
    
    Args:
        model_config ([type]): [description]
    
    Returns:
        [type]: [description]
    """
    model_class = model_config.pop('class', 'SeparationModel')
    ModelClass = getattr(model, model_class)
    if model_class == 'SeparationModel':
        model_instance = ModelClass(model_config, extra_modules=model.extras)
    else:
        model_instance = ModelClass(model_config)
    return model_instance