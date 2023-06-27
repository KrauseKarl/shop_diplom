from app_compare.compare import Comparison


def compare_list(request):
    compares = Comparison(request)
    return {'compare_count': compares.__len__(), 'compare_item': compares}
