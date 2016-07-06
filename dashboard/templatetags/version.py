from django import template
import time
import os
import laboratory

register = template.Library()

@register.simple_tag
def version_date():
    return "%s %s" % (laboratory.VERSION, time.strftime('%m/%d/%Y', time.gmtime(os.path.getmtime('../.git'))))