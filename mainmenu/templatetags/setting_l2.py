from appconf.manager import SettingManager
from django import template

register = template.Library()


@register.simple_tag(name='s_l2')
def s_l2(key):
    return SettingManager.l2(key)
