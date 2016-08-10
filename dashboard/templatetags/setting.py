from appconf.manager import SettingManager
from django import template

register = template.Library()


@register.simple_tag
def s_get(key):
    return SettingManager.get(key)
