from urllib.parse import urlencode
from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    pass
    # query = context['request'].GET.copy()
    # try:
    #     query = context['request'].GET.copy()
    #     if kwargs['page']:
    #         res = query.pop('page')
    #         query.update(kwargs)
    #     if kwargs['order_by']:
    #         res = query.pop('order_by')
    #     query.update(kwargs)
    #     if kwargs['price']:
    #         minn = kwargs['price'].splite(';')[0]
    #         maxx = kwargs['price'].splite(';')[1]
    #         path = f'&price={minn}%3B{maxx}'
    #         query.update(path)
    #     return query.urlencode()
    # except KeyError:
    #     pass
