"""
URL configuration for telecom_ai_agent project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

import os
import socket
from pathlib import Path

from django.core.cache import cache
from django.db import connection
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import path, re_path, include
from django.views import static
from rest_framework import status

from chat.urls import urlpatterns as chat_urlpatterns
from common.init.init_doc import init_doc
from common.result import Result
from telecom_ai_agent import settings
from telecom_ai_agent.conf import PROJECT_DIR
from telecom_ai_agent.const import CONFIG
from telecom_ai_agent.env import get_env

admin_api_prefix = CONFIG.get_admin_path()[1:] + "/api/"
admin_ui_prefix = CONFIG.get_admin_path()
chat_api_prefix = CONFIG.get_chat_path()[1:] + "/api/"
chat_ui_prefix = CONFIG.get_chat_path()


def healthz(_request):
    """Container readiness probe without exposing connection details."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        cache_key = "deployment:healthz"
        cache.set(cache_key, "ok", timeout=10)
        if cache.get(cache_key) != "ok":
            raise RuntimeError("cache round trip failed")
        if str(get_env("TELECOM_AI_START_LOCAL_MODEL", "false")).strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }:
            with socket.create_connection(
                (CONFIG.get("LOCAL_MODEL_HOST"), int(CONFIG.get("LOCAL_MODEL_PORT"))),
                timeout=2,
            ):
                pass
    except Exception:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})


def serve_locale_file(request, path="index.json"):
    """Serve optional external locale files without turning missing index.json into a page 404."""
    root = os.path.join(PROJECT_DIR, "apps", "static", "admin", "locales")
    requested_path = os.path.join(root, path)
    if os.path.isfile(requested_path):
        return static.serve(request, path, document_root=root)
    if path == "index.json":
        return JsonResponse({"locales": []})
    return HttpResponse("Not Found", status=404)


urlpatterns = [
    path("healthz", healthz, name="healthz"),
    re_path(r"^locales/(?P<path>.*)$", serve_locale_file),
    re_path(rf"^{admin_ui_prefix[1:]}/locales/(?P<path>.*)$", serve_locale_file),
    re_path(rf"^{chat_ui_prefix[1:]}/locales/(?P<path>.*)$", serve_locale_file),
    path(admin_api_prefix, include("users.urls")),
    path(admin_api_prefix, include("tools.urls")),
    path(admin_api_prefix, include("models_provider.urls")),
    path(admin_api_prefix, include("folders.urls")),
    path(admin_api_prefix, include("knowledge.urls")),
    path(admin_api_prefix, include("system_manage.urls")),
    path(admin_api_prefix, include("application.urls")),
    path(admin_api_prefix, include("trigger.urls")),
    path(admin_api_prefix, include("oss.urls", namespace="admin_oss")),
    path(admin_api_prefix, include("homepage.urls")),
    path(admin_api_prefix, include("marketing.urls")),
    path(admin_api_prefix, include("platform_monitoring.urls")),
    path(admin_api_prefix, include("rehearsal.urls")),
    path(admin_api_prefix, include("xpack_lite.urls")),
    path(chat_api_prefix, include("oss.urls", namespace="chat_oss")),
    path(chat_api_prefix, include("xpack_lite.chat_urls")),
    path(chat_api_prefix, include("chat.urls")),
    path(f"{admin_ui_prefix[1:]}/", include("oss.retrieval_urls", namespace="admin_oss_retrieval")),
    path(f"{chat_ui_prefix[1:]}/", include("oss.retrieval_urls", namespace="chat_oss_retrieval")),
]
init_doc(urlpatterns, chat_urlpatterns)


def append_api_doc_static():
    urlpatterns.append(
        re_path(
            rf"^{CONFIG.get_admin_path()[1:]}/api-doc/(?P<path>.*)$",
            static.serve,
            {"document_root": os.path.join(settings.STATIC_ROOT, "drf_spectacular_sidecar")},
            name="doc",
        ),
    )

    urlpatterns.append(
        re_path(
            rf"^{CONFIG.get_chat_path()[1:]}/api-doc/(?P<path>.*)$",
            static.serve,
            {"document_root": os.path.join(settings.STATIC_ROOT, "drf_spectacular_sidecar")},
            name="doc_chat",
        ),
    )


def pro():
    append_api_doc_static()
    # 暴露ui静态资源
    urlpatterns.append(
        re_path(rf"^{CONFIG.get_admin_path()[1:]}/(?P<path>.*)$", serve_admin_spa, name="admin"),
    )
    # 暴露ui静态资源
    urlpatterns.append(
        re_path(rf"^{CONFIG.get_chat_path()[1:]}/(?P<path>.*)$", serve_chat_spa, name="chat"),
    )


def get_index_html(index_path):
    file = open(index_path, "r", encoding="utf-8")
    content = file.read()
    file.close()
    return content


def get_all_files(directory):
    base_path = Path(directory)
    file_paths = [
        "/" + str(file.relative_to(base_path)).replace("\\", "/") for file in base_path.rglob("*") if file.is_file()
    ]
    return sorted(file_paths, key=len, reverse=True)


static_dict = {
    chat_ui_prefix: get_all_files(os.path.join(PROJECT_DIR, "apps", "static", "chat")),
    admin_ui_prefix: get_all_files(os.path.join(PROJECT_DIR, "apps", "static", "admin")),
}


def serve_spa(request, path, root, index_path, prefix):
    """Serve the built SPA in both DEBUG and production modes."""
    requested_path = os.path.join(root, path) if path else ""
    if path and os.path.isfile(requested_path):
        return static.serve(request, path, document_root=root)
    if not os.path.isfile(index_path):
        return HttpResponse("页面不存在", status=404)
    content = get_index_html(index_path).replace("prefix: '/admin'", f"prefix: '{prefix}'")
    # 构建产物使用相对资源路径；深层前端路由下需要改为从应用根路径加载，
    # 否则 /admin/system/user 会把脚本请求成 /admin/system/assets/... 导致白屏。
    content = content.replace('src="./', f'src="{prefix}/').replace('href="./', f'href="{prefix}/')
    if prefix == CONFIG.get_admin_path():
        content = content.replace("chatPrefix: '/chat'", f"chatPrefix: '{CONFIG.get_chat_path()}'")
    return HttpResponse(content, status=200)


def serve_admin_spa(request, path=""):
    root = os.path.join(PROJECT_DIR, "apps", "static", "admin")
    return serve_spa(request, path, root, os.path.join(root, "index.html"), CONFIG.get_admin_path())


def serve_chat_spa(request, path=""):
    root = os.path.join(PROJECT_DIR, "apps", "static", "chat")
    return serve_spa(request, path, root, os.path.join(root, "index.html"), CONFIG.get_chat_path())


if not settings.DEBUG:
    pro()
else:
    append_api_doc_static()
    urlpatterns.append(
        re_path(rf"^{CONFIG.get_admin_path()[1:]}/(?P<path>(?!(?:api|api-doc)(?:/|$)).*)$", serve_admin_spa),
    )
    urlpatterns.append(
        re_path(rf"^{CONFIG.get_chat_path()[1:]}/(?P<path>(?!(?:api|api-doc)(?:/|$)).*)$", serve_chat_spa),
    )


def page_not_found(request, exception):
    """
    页面不存在处理
    """
    if request.path.startswith(admin_ui_prefix + "/api/"):
        return Result(response_status=status.HTTP_404_NOT_FOUND, code=404, message="HTTP_404_NOT_FOUND")
    if request.path.startswith(chat_ui_prefix + "/api/"):
        return Result(response_status=status.HTTP_404_NOT_FOUND, code=404, message="HTTP_404_NOT_FOUND")
    if request.path.startswith(chat_ui_prefix):
        in_ = [url for url in static_dict.get(chat_ui_prefix) if request.path.endswith(url)]
        if len(in_) > 0:
            a = chat_ui_prefix + in_[0]
            return HttpResponseRedirect(a)
        index_path = os.path.join(PROJECT_DIR, "apps", "static", "chat", "index.html")
        content = get_index_html(index_path)
        content = content.replace("prefix: '/chat'", f"prefix: '{CONFIG.get_chat_path()}'")
        if not os.path.exists(index_path):
            return HttpResponse("页面不存在", status=404)
        return HttpResponse(content, status=200)
    elif request.path.startswith(admin_ui_prefix):
        in_ = [url for url in static_dict.get(admin_ui_prefix) if request.path.endswith(url)]
        if len(in_) > 0:
            a = admin_ui_prefix + in_[0]
            return HttpResponseRedirect(a)
        index_path = os.path.join(PROJECT_DIR, "apps", "static", "admin", "index.html")
        if not os.path.exists(index_path):
            return HttpResponse("页面不存在", status=404)
        content = get_index_html(index_path)
        content = content.replace("prefix: '/admin'", f"prefix: '{CONFIG.get_admin_path()}'").replace(
            "chatPrefix: '/chat'", f"chatPrefix: '{CONFIG.get_chat_path()}'"
        )
        return HttpResponse(content, status=200)
    else:
        return HttpResponseRedirect(admin_ui_prefix + "/")


handler404 = page_not_found
