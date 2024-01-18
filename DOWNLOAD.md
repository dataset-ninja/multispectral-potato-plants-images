Dataset **Multispectral Potato Plants Images** can be downloaded in [Supervisely format](https://developer.supervisely.com/api-references/supervisely-annotation-json-format):

 [Download](https://assets.supervisely.com/supervisely-supervisely-assets-public/teams_storage/G/7/mJ/DjSVdqi4R2zdZF2GhxT7UOm6XlzCcZSDuWld9Nmrh3vwRBljudydEuTyNUfH5ERoqx8iFdqGWfu0PBuF6CxoXgQWNQYqf5wAZtAbKFaA65Nm9PGreaOshsmEqDOO.tar)

As an alternative, it can be downloaded with *dataset-tools* package:
``` bash
pip install --upgrade dataset-tools
```

... using following python code:
``` python
import dataset_tools as dtools

dtools.download(dataset='Multispectral Potato Plants Images', dst_dir='~/dataset-ninja/')
```
Make sure not to overlook the [python code example](https://developer.supervisely.com/getting-started/python-sdk-tutorials/iterate-over-a-local-project) available on the Supervisely Developer Portal. It will give you a clear idea of how to effortlessly work with the downloaded dataset.

The data in original format can be downloaded here:

- [RGB Image Patches (38 MB)](https://www.webpages.uidaho.edu/vakanski/Codes_Data/RGB_Images.zip)
- [RGB Image Patches - Augmented Dataset (199 MB)](https://www.webpages.uidaho.edu/vakanski/Codes_Data/RGB_Augmented.zip)
- [Spectral Image Patches (46 MB)](https://www.webpages.uidaho.edu/vakanski/Codes_Data/Spectral_Images.zip)
- [Spectral Image Patches - Augmented Dataset (248 MB)](https://www.webpages.uidaho.edu/vakanski/Codes_Data/Spectral_Augmented.zip)
