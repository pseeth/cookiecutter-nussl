from .. import dataset, model

def load_dataset(dataset_class, dataset_folder, dataset_config):
    DatasetClass = getattr(dataset, dataset_class)
    dataset_instance = DatasetClass(dataset_folder, dataset_config)
    return dataset_instance

def load_model(model_config):
    model_class = model_config.pop('class', 'SeparationModel')
    ModelClass = getattr(model, model_class)
    if model_class == 'SeparationModel':
        model_instance = ModelClass(model_config, extra_modules=model.extras)
    else:
        model_instance = ModelClass(model_config)
    return model_instance