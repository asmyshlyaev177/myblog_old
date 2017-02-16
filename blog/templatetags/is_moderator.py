from django import template

register = template.Library()


@register.filter(name="is_moderator")
def is_moderator(user, obj):
    return user.is_moderator(obj)
