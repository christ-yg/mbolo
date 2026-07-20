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
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

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
    	"api/v1/safety/",
    	include("apps.safety.urls"),
    ),

    path(
    	"api/v1/profiles/photos/",
    	include("apps.photos.urls"),
    ),

]


# Django sert les médias uniquement pendant le développement local.
#
# En production, cette responsabilité sera confiée à un stockage
# d'objets, un CDN ou un proxy web sécurisé.
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
