from django.contrib import admin
from .models import Poll, Question, MyUser
from django.contrib.auth.admin import UserAdmin


class MyUserAdmin(UserAdmin):
    model = MyUser


admin.site.register(MyUser, MyUserAdmin)
admin.site.register(Poll)
admin.site.register(Question)
