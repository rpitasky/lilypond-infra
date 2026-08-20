from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, JsonResponse

from extern.lilypond_render import git_pull, git_tags


# Create your views here.
@staff_member_required
def trigger_git_pull(request):
    try:
        result = git_pull()
    except Exception as e:
        return HttpResponse(f"Error: {e}", status=500)

    return JsonResponse(result)


@staff_member_required
def list_git_tags(request):
    try:
        result = git_tags()
    except Exception as e:
        return HttpResponse(f"Error: {e}", status=500)

    return JsonResponse(result)
