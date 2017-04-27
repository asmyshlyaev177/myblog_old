from django import template
from blog.views import user_has_rights
register = template.Library()


@register.filter(name="is_moderator")
def is_moderator(user, obj):
    return user_has_rights(user, obj)
