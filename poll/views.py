from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import date
from django.db.models import Q

from .models import Poll, Question, Attempt
from .permissions import IsAdminOrReadOnly
from .serializers import PollSerializer, WriteQuestionSerializer, PollDetailSerializer, AttemptSerializer, \
    VoteSerializer


class PollViewSet(viewsets.ModelViewSet):
    serializer_class = PollSerializer
    permission_classes = (IsAdminOrReadOnly, )
    http_method_names = ['get', 'post', 'head', 'delete', 'patch']

    def get_queryset(self):
        if self.request.user.is_staff:
            queryset = Poll.objects.all()
        else:
            queryset = Poll.objects.filter(Q(finished_at__gt=date.today()) | Q(finished_at__isnull=True))
        return queryset

    def has_permission(self, request, view):
        if view.action in ['retrieve', 'list']:
            return True
        elif view.action in ['update', 'partial_update', 'destroy', 'create']:
            return bool(request.user and request.user.is_staff)
        else:
            return False

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PollDetailSerializer
        else:
            return PollSerializer

    @action(methods=['post'], detail=True, permission_classes=[AllowAny])
    def vote(self, request,  *args, **kwargs):
        serializer = VoteSerializer(data=request.data, context={'poll_pk': self.kwargs['pk']})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = WriteQuestionSerializer
    permission_classes = (IsAdminUser, )
    lookup_field = 'position'
    http_method_names = ['get', 'post', 'head', 'delete', 'patch']

    def get_queryset(self):
        return Question.objects.filter(poll=self.kwargs['poll_pk']).order_by('position')

    def get_serializer_context(self):
        context = super(QuestionViewSet, self).get_serializer_context()
        context.update({'poll_pk': self.kwargs['poll_pk']})
        return context


class AttemptAPIView(APIView):

    def post(self, request, *args, **kwargs):
        user = request.data.get('user', None)
        if user:
            queryset = Attempt.objects.filter(user=user)
            serializer = AttemptSerializer(queryset, many=True)
            return Response(serializer.data)
        else:
            return Response(r'"detail": "User id is required"')
