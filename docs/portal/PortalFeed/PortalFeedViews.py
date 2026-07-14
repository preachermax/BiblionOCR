from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt


def build_portal_feed_payload():
    return {
        "title": "Biblion Portal Feed",
        "panels": {
            "main": {
                "html": (
                    "<h1>Portal Landing Feed</h1>"
                    "<p>This primary panel is intended for the launcher landing page.</p>"
                )
            },
            "secondary": {
                "html": (
                    "<h3>Project Status</h3>"
                    "<ul><li>OCR queue healthy</li><li>Trainer idle</li></ul>"
                )
            },
            "tertiary": {
                "html": (
                    "<h3>Recent Activity</h3>"
                    "<p>Use this card for announcements, tasks, or community notices.</p>"
                )
            },
        },
    }


def portal_preview_page(request):
    return render(
        request,
        "portal_preview_harness.html",
        {
            "page_title": "Biblion Portal Preview Harness",
            "feed_endpoint": request.GET.get("feed", "/portal/feed/"),
        },
    )


def get_html_view(request):
    if "application/json" in request.headers.get("Accept", ""):
        return JsonResponse(build_portal_feed_payload())

    dynamic_html = "<h1>Dashboard</h1><p>Sent directly from Django!</p>"
    return HttpResponse(dynamic_html, content_type="text/html")


@csrf_exempt
def post_html_view(request):
    if request.method == "POST":
        received_html = request.POST.get("html_content", "")
        print(received_html)
        return HttpResponse("Saved successfully", status=200)

    return HttpResponse(status=405)