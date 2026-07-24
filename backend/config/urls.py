"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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


from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.contrib.staticfiles.views import serve as serve_static


# Identité textuelle de l'espace d'administration.
admin.site.site_header = "Administration Mbolo"
admin.site.site_title = "Mbolo Admin"
admin.site.index_title = "Pilotage sécurisé de la plateforme"

urlpatterns = [
    path(
        "admin/",
        admin.site.urls,
    ),

    path(
        "api/v1/",
        include("apps.core.urls"),
    ),

    path(
        "api/v1/auth/",
        include("apps.accounts.urls"),
    ),
    path(
        "api/v1/profiles/",
        include("apps.profiles.urls"),
    ),
    path(
        "api/v1/",
        include("apps.interactions.urls"),
    ),
    path(
        "api/v1/",
        include("apps.messaging.urls"),
    ),

    path(
        "api/v1/",
        include("apps.notifications.urls"),
    ),

    path(
    	"api/v1/safety/",
    	include("apps.safety.urls"),
    ),

    path(
    	"api/v1/profiles/photos/",
    	include("apps.photos.urls"),
    ),
    path(
        "api/v1/premium/",
        include("apps.subscriptions.urls"),
    ),

]


# Django sert les médias uniquement lorsque le mode de développement ou le
# réglage local explicite est actif.
#
# En production, cette responsabilité sera confiée à un stockage
# d'objets, un CDN ou un proxy web sécurisé.
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
elif settings.SERVE_MEDIA_LOCALLY:
    # django.conf.urls.static.static() retourne volontairement une liste vide
    # lorsque DEBUG=False. Cette route explicite est donc réservée au serveur
    # local et n'est créée que si SERVE_MEDIA_LOCALLY=True dans le .env.
    urlpatterns += [
        re_path(
            r"^media/(?P<path>.*)$",
            serve,
            {
                "document_root": settings.MEDIA_ROOT,
            },
        ),
        # APP_DEBUG reste volontairement désactivé. Cette route locale sert
        # néanmoins les ressources CSS/JS de Django et notre thème Mbolo.
        # Elle n'est active que lorsque SERVE_MEDIA_LOCALLY=True et devra être
        # remplacée en production par Nginx/WhiteNoise/CDN.
        re_path(
            r"^static/(?P<path>.*)$",
            serve_static,
            {"insecure": True},
        ),
    ]
