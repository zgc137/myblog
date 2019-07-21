from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser,UserManager as _UserManager
# Create your models here.
# is_staff   用户是否可以登录admin管理界面
# is_active  用户是否活跃


class UserManage(_UserManager):   # 方法重写

    def create_superuser(self, username, password,email=None, **extra_fields):

        # 调用super方法
        super().create_superuser(username=username,password=password,email=email, **extra_fields)


class User(AbstractUser):
    """
    add mobile email_active fields to Django users models
    """
    objects = UserManage()

    REQUIRED_FIELDS = ['mobile']   # 指定注册账户

    mobile = models.CharField(max_length=11,unique=True,verbose_name='手机号',
                              help_text='手机号',error_messages={'unique':'此手机号已被注册'})
    email_active = models.BooleanField(default=False,verbose_name='邮箱验证状态')

    class Meta:
        db_table = 'tb_users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name  # 显示的复数名称

    def __str__(self):
        return self.username

