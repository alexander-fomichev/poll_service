from django.db import models
from datetime import date
from django.conf import settings
from django.contrib.auth.models import AbstractUser


class MyUser(AbstractUser):

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []


class Poll(models.Model):
    title = models.CharField(max_length=50, verbose_name='Название')
    description = models.TextField(null=True, blank=True, verbose_name='Описание')
    # is_active = models.BooleanField(default=True)
    started_at = models.DateField(auto_now_add=True, verbose_name='Дата старта')
    finished_at = models.DateField(null=True, blank=True, verbose_name='Дата окончания')

    class Meta:
        verbose_name = 'Опрос'
        verbose_name_plural = 'Опросы'
        ordering = ['-started_at', ]

    @property
    def is_active(self):
        """Is the poll active?
        """
        is_active = not self.finished_at or (self.finished_at > date.today())
        return is_active

    def __str__(self):
        return self.title


class Question(models.Model):
    TEXT = 1
    SINGLE_CHOICE = 2
    MULTI_CHOICE = 3
    QUESTION_TYPES = (
        (TEXT, 'Ответ текстом'),
        (SINGLE_CHOICE, 'Ответ с выбором одного варианта'),
        (MULTI_CHOICE, 'Ответ с выбором нескольких вариантов'),
    )

    position = models.IntegerField(verbose_name='Номер вопроса в опросе')
    question_type = models.SmallIntegerField(choices=QUESTION_TYPES, default=TEXT)
    main_text = models.TextField(verbose_name='Текст вопроса')
    poll = models.ForeignKey('Poll', on_delete=models.CASCADE, verbose_name='Опрос', related_name='questions')

    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'


class Choice(models.Model):
    choice_text = models.CharField(max_length=50, verbose_name='Текст варианта ответа',)
    question = models.ForeignKey('Question', on_delete=models.CASCADE, verbose_name='Вопрос', related_name='choices')

    def __str__(self):
        return self.choice_text


class Attempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Пользователь',
                             related_name='attempts')
    poll = models.ForeignKey('Poll', on_delete=models.CASCADE, verbose_name='Опрос')
    time = models.DateTimeField(auto_now_add=True,)
    ordering = ['-time', ]


class Answer(models.Model):
    attempt = models.ForeignKey('Attempt', on_delete=models.CASCADE, verbose_name='Попытка', related_name='answers')
    question = models.ForeignKey('Question', on_delete=models.CASCADE, verbose_name='Вопрос')
    answer = models.TextField(verbose_name='Ответ',)
