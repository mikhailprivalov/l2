import logging
from typing import Callable, Dict, Union
from django.db import models

import simplejson
from django.http import Http404

from clients.models import Card


logger = logging.getLogger(__name__)


def as_model(model: models.Model):
    def internal(pk: Union[int, str]):
        return model.objects.filter(pk=pk).first()

    return internal


def data_parse(data: Union[dict, str, bytes], keys_types: Dict[str, Union[Callable, str, None]], default_values: dict = None) -> list:
    """
    Функиця проверки типов.
    >>> request_data = {'s': 'string', 'i': 15, 'f': 15.5, 'l': [1, 2, 3], 'd': {1: 1, 2: 2}}
    >>> type_dict = {'s': str, 'i': int, 'f': float, 'l': list, 'd': dict}
    >>> data_parse(request_data, type_dict)
    """
    if isinstance(data, bytes):
        data = data.decode('utf-8')

    if isinstance(data, str):
        data = simplejson.loads(data)

    typed_vars = []
    if default_values is None:
        default_values = {}
    elif not isinstance(default_values, dict):
        raise TypeError('Error, default_values must be dict')

    for key, var_type in keys_types.items():
        var = data.get(key, default_values.get(key))
        try:
            if type(var) is var_type:
                typed_vars.append(var)
            else:
                if key not in data and key not in default_values:
                    error = f'{key}: {var} not found!'
                    logger.exception(error)
                    raise Http404(error)
                if var_type is None or (var is None and default_values.get(key, True) is None):
                    typed_vars.append(None)
                elif var_type == 'str_strip':
                    typed_vars.append(str(var).strip())
                elif var_type == 'card':
                    typed_vars.append(Card.objects.get(pk=var))
                else:
                    typed_vars.append(var_type(var))
        except TypeError or ValueError:
            error = f'Cannot cast type Key: {key}, Value: {var}, Type: {var_type}'
            logger.exception(error)
            raise Http404(error)
    return typed_vars
