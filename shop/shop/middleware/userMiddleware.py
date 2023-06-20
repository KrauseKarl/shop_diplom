from django.shortcuts import redirect


def simple_middleware(get_response):

    def middleware(request):
        response = get_response(request)
        if request.user.is_authenticated:
            if not request.user.profile.is_active:
                if request.path != '/accounts/block_page/':
                    return redirect('app_user:block_page')
        return response

    return middleware
