from django.urls import include, path

urlpatterns += [
    path(
        "compliance/hipaa/",
        include("compliance.hipaa.urls", namespace="hipaa_compliance"),
    ),
]
