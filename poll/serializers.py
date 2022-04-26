from rest_framework import serializers
from .models import Poll, Question, Choice, Attempt, Answer, MyUser
from django.contrib.auth import get_user_model

UserModel = get_user_model()


class PollSerializer(serializers.ModelSerializer):
    class Meta:
        model = Poll
        exclude = ['id', ]


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['choice_text', ]


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True)
    question_type = serializers.CharField(source='get_question_type_display')

    def get_question_type(self, obj):
        return obj.get_question_type_display()

    class Meta:
        model = Question
        fields = ['position', 'question_type', 'main_text', 'choices']


class WriteQuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True)

    class Meta:
        model = Question
        fields = ['position', 'question_type', 'main_text', 'choices', ]

    def create(self, validated_data):
        """ Создать запись вопроса"""

        # Достаем id Опроса из контекста и добавляем его в набор данных для записи:
        poll_id = self.context.get('poll_pk')
        if poll_id is None:
            raise serializers.ValidationError("Must set the poll_pk kwarg to use this serializer.")
        validated_data['poll'] = Poll.objects.get(pk=poll_id)

        # Создаем соответствующие записи в таблице Choice:
        choices_data = validated_data.pop('choices')
        question = Question.objects.create(**validated_data)
        for choice_data in choices_data:
            Choice.objects.create(question=question, **choice_data)
        return question

    def update(self, instance, validated_data):
        instance.question_type = validated_data.get('question_type', instance.question_type)
        instance.main_text = validated_data.get('main_text', instance.main_text)
        instance.position = validated_data.get('position', instance.position)
        instance.save()

        choices = validated_data.get('choices', None)
        # Если нужно вписать новые либо если варианты ответа не нужны, то удаляем старые значения вариантов ответа:
        if choices is not None or instance.question_type == Question.TEXT[0]:
            Choice.objects.filter(question=instance).delete()
            for choice in choices:
                Choice.objects.create(question=instance, **choice)
        return instance

    def validate_position(self, value):
        """
        Проверяет уникальность номера вопроса (position) в опросе
        """
        poll_id = self.context.get('poll_pk')
        if value and Question.objects.filter(poll_id=poll_id, position=value).exists():
            raise serializers.ValidationError("Position already exists!")
        return value

    def validate_question_type(self, value):
        """
        Проверяет что тип вопроса имеет допустимое значение
        """
        types = [x[0] for x in Question.QUESTION_TYPES]
        if value not in types:
            raise serializers.ValidationError("Invalid question type value")
        return value

    def validate(self, data):
        """
        Проверяет наличие вариантов ответа у вопросов с выбором ответа
        """
        if data['question_type'] in (2, 3):
            if len(data['choices']) < 2:
                raise serializers.ValidationError("This type of question must have at least 2 choices")
        else:
            if data['choices'] is not None:
                raise serializers.ValidationError("This type of question haven't choices")

        return data


class PollDetailSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True)

    class Meta:
        model = Poll
        fields = ['id', 'title', 'description', 'started_at', 'finished_at', 'questions']


# class AnswerSerializer(serializers.ModelSerializer):
#     position = serializers.IntegerField(read_only=True, required=False)
#     question = serializers.SerializerMethodField('get_question')
#     answer = serializers.SerializerMethodField('get_answer')
#
#     def get_question(self, obj):
#         position = self.fields.get('position')
#         poll = self.context.get('poll_pk', None)
#         question = Question.objects.get(position=position, poll=poll)
#         return question
#
#     def get_answer(self, obj):
#         answers = self.fields.get('answer')
#         answer_str = '; '.join(str(answer) for answer in answers)
#         return answer_str[:-2]
#
#     class Meta:
#         model = Answer
#         fields = ['id', 'question', 'answer', 'position']


class VoteSerializer(serializers.ModelSerializer):
    # answers = AnswerSerializer(many=True)
    answers = serializers.ListField(write_only=True)

    class Meta:
        model = Attempt
        fields = ['id', 'user', 'poll', 'answers']
        extra_kwargs = {'user': {'allow_null': True},
                        'poll': {'required': False},
                        }

    def create(self, validated_data):
        """ Создать записи попытки и ответов"""

        # Достаем id Опроса из контекста и добавляем его в набор данных для записи:
        poll_pk = self.context.get('poll_pk')
        poll = Poll.objects.get(pk=poll_pk)
        answers_data = validated_data['answers']

        # Если пользователь авторизован, меняем контекст запроса:
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
        # Если пользователь не указан создаем нового c username=id:
        elif not validated_data['user']:
            user = MyUser.objects.create_user(username='auto_username')
            user.username = str(user.id)
            user.save()
            validated_data['user'] = user

        # Создаем соответствующие записи в таблице Answer:
        attempt = Attempt.objects.create(user=validated_data['user'], poll=poll)
        for answer_data in answers_data:
            question = Question.objects.get(position=answer_data['position'], poll=poll)
            Answer.objects.create(attempt=attempt, question=question, answer=answer_data['answer'])
        if attempt:
            print(attempt)
        else:
            print('None')
        return attempt

    def validate_user(self, value):
        """
        Проверяем что User есть в БД или значение пустое
        """
        if value:
            try:
                value.id
            except UserModel.DoesNotExist:
                raise serializers.ValidationError("User doesn't exists")
        return value

    def validate(self, data):
        """

        """

        poll_pk = self.context.get('poll_pk', None)
        poll = Poll.objects.get(pk=poll_pk)
        if not poll:
            raise serializers.ValidationError("Poll #" + str(poll_pk) + " doesn't exists")
        if not poll.is_active:
            raise serializers.ValidationError("Poll #" + str(poll_pk) + " is not active")

        question_list = Question.objects.filter(poll=poll_pk)
        question_ids = [q.id for q in question_list]
        if not question_ids:
            raise serializers.ValidationError("Poll #" + str(poll_pk) + " doesn't have questions")
        answers = data['answers']
        for answer in answers:

            position = answer['position']
            try:
                question = Question.objects.get(position=position, poll=poll_pk)
            except Question.DoesNotExist:
                raise serializers.ValidationError("Question #" + str(position) + " doesn't exists")
            question_ids.remove(question.id)
            if question.question_type in (1, 2) and len(answer['answer']) != 1:
                raise serializers.ValidationError("Question #" + str(position) + " required one answer")
            elif question.question_type == 3 and len(answer['answer']) == 0:
                raise serializers.ValidationError("Question #" + str(position) + " required at least one answer")

            if question.question_type in (2, 3):
                choices = Choice.objects.filter(question=question)
                possible_answers = [q.choice_text for q in choices]
                for part_answer in answer['answer']:
                    if part_answer not in possible_answers:
                        raise serializers.ValidationError("Question #" + str(position) + ": invalid answer")

        if question_ids:
            raise serializers.ValidationError("You must answer every question")

        return data


class AnswerSerializer(serializers.ModelSerializer):
    question = QuestionSerializer()

    class Meta:
        model = Answer
        fields = ['question', 'answer']


class AttemptSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True)
    poll = PollSerializer()
    time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = Attempt
        fields = ['user', 'time', 'poll', 'answers']
