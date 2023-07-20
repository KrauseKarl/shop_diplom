from app_favorite.favorites import Favorite


def favorites(request):
    favorites_item = Favorite(request)
    return {"favorites_count": favorites_item.__len__(), "favorites": favorites_item}
