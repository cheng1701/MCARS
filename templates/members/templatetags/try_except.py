from django import template
from django.template.base import Node, NodeList, TemplateSyntaxError

register = template.Library()

class TryExceptNode(Node):
    def __init__(self, try_nodes, except_nodes):
        self.try_nodes = try_nodes
        self.except_nodes = except_nodes

    def render(self, context):
        try:
            return self.try_nodes.render(context)
        except Exception:
            return self.except_nodes.render(context)

@register.tag('try')
def do_try(parser, token):
    """
    The ``{% try %} ... {% except %} ... {% endtry %}`` tag.

    This tag works like Python's try/except statement. If the content of the
    try block raises an exception, the content of the except block is rendered
    instead.

    Usage::

        {% try %}
            {{ member.rank_association.rank.short_name }}
        {% except %}
            No rank assigned
        {% endtry %}
    """
    bits = token.split_contents()
    if len(bits) != 1:
        raise TemplateSyntaxError("'%s' takes no arguments" % bits[0])

    try_nodes = parser.parse(('except',))
    parser.delete_first_token()
    except_nodes = parser.parse(('endtry',))
    parser.delete_first_token()

    return TryExceptNode(try_nodes, except_nodes)
