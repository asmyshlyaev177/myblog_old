from django import template

register = template.Library()


@register.inclusion_tag('partials/post_header.html', takes_context=True)
def post_header(context):
    return {
    'post': context['post'],
    }
