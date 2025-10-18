from django import template
from django.template import Node, NodeList, TemplateSyntaxError

register = template.Library()

class TryNode(Node):
    def __init__(self, try_nodelist, except_nodelist=None):
        self.try_nodelist = try_nodelist
        self.except_nodelist = except_nodelist

    def render(self, context):
        try:
            return self.try_nodelist.render(context)
        except Exception:
            if self.except_nodelist:
                return self.except_nodelist.render(context)
            return ''
from django import template
from django.template import Node, NodeList, TemplateSyntaxError

register = template.Library()

class TryNode(Node):
    def __init__(self, try_nodelist, except_nodelist):
        self.try_nodelist = try_nodelist
        self.except_nodelist = except_nodelist

    def render(self, context):
        try:
            return self.try_nodelist.render(context)
        except Exception:
            return self.except_nodelist.render(context)

@register.tag('try')
def do_try(parser, token):
    """Try/except block for templates"""
    try_nodelist = parser.parse(('except',))
    parser.delete_first_token()
    except_nodelist = parser.parse(('endtry',))
    parser.delete_first_token()
    return TryNode(try_nodelist, except_nodelist)
@register.tag('try')
def do_try(parser, token):
    """Try/except block for templates"""
    try_nodelist = parser.parse(('except', 'endtry'))
    token = parser.next_token()

    if token.contents == 'except':
        except_nodelist = parser.parse(('endtry',))
        parser.delete_first_token()
    else:
        except_nodelist = None

    return TryNode(try_nodelist, except_nodelist)
