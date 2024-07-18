# App level urls

from django.urls import path
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from . import views
from .views import *

urlpatterns = [
    path('', login_required(views.index), name='index'),
    path('ideation/', login_required(views.ideation), name='ideation'),
    path('meaning_making/', login_required(views.meaning_making), name='meaning_making'),
    path('interaction/', login_required(views.interaction), name='interaction'),

    # ... API Paths
    path('api/', APIRootView.as_view(), name='api_root'),
    path('api/generate-background-story/', GenerateBackgroundStoryAPIView.as_view(), name='generate_background_story_api'),
    path('api/refine-background-story/', RefineBackgroundStoryAPIView.as_view(), name='refine_background_story_api'),
    path('api/generate-protostory/', GenerateProtoStoryAPIView.as_view(), name='generate_protostory_api'),
    path('api/refine-protostory/', RefineProtoStoryAPIView.as_view(), name='refine_protostory_api'),
    path('api/analyze-protostory-coherence/', AnalyzeNarrativeCoherenceAPIView.as_view(), name='analyze-protostory-coherence_api'),
]

urlpatterns += staticfiles_urlpatterns()








