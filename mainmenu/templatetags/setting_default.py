from appconf.manager import SettingManager
from django import template

register = template.Library()


@register.simple_tag(name='s_default')
def s_default(key, default=None, default_type='s'):
    return SettingManager.get(key, default, default_type)
