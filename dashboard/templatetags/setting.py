from appconf.manager import SettingManager
from django import template

register = template.Library()


@register.simple_tag(name='s_get')
def s_get(key):
    return SettingManager.get(key)
