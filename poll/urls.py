from django.urls import path, include
# from rest_framework import routers
from rest_framework_nested import routers

from .views import PollViewSet, QuestionViewSet, AttemptAPIView

router = routers.DefaultRouter()
router.register(r'polls', PollViewSet, basename='poll')

question_router = routers.NestedSimpleRouter(router, r'polls', lookup='poll')
question_router.register(r'questions', QuestionViewSet, basename='questions')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(question_router.urls)),
    path('results/', AttemptAPIView.as_view()),
]
