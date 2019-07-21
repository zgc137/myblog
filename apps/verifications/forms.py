
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-------------------------------------------------

-------------------------------------------------
"""
from django import forms
from django.core.validators import RegexValidator
from django_redis import get_redis_connection

from users.models import User

# 创建手机号的正则校验器
mobile_validator = RegexValidator(r"^1[3-9]\d{9}$", "手机号码格式不正确")


class CheckImgCodeForm(forms.Form):
    """
    check image code
    """
    mobile = forms.CharField(max_length=11, min_length=11, validators=[mobile_validator, ],
                             error_messages={"min_length": "手机号长度有误", "max_length": "手机号长度有误",
                                             "required": "手机号不能为空"})
    image_code_id = forms.UUIDField(error_messages={"required": "图片UUID不能为空"})
    text = forms.CharField(max_length=4, min_length=4,
                           error_messages={"min_length": "图片验证码长度有误", "max_length": "图片验证码长度有误",
                                           "required": "图片验证码不能为空"})

    # Cleaning and validating fields that depend on each other
    def clean(self):
        cleaned_data = super().clean()
        # 1、
        image_uuid = cleaned_data.get("image_code_id")
        image_text = cleaned_data.get("text")
        mobile_num = cleaned_data.get("mobile")

        # 2、
        if User.objects.filter(mobile=mobile_num).count():
            raise forms.ValidationError("手机号已注册，请重新输入")

        # 确保settings.py文件中有配置redis CACHE
        # Redis原生指令参考 http://redisdoc.com/index.html
        # Redis python客户端 方法参考 http://redis-py.readthedocs.io/en/latest/#indices-and-tables
        # 2、
        con_redis = get_redis_connection(alias='verify_codes')
        # 创建保存到redis中图片验证码的key
        img_key = "img_{}".format(image_uuid).encode('utf-8')

        # 取出图片验证码
        real_image_code_origin = con_redis.get(img_key)
        real_image_code = real_image_code_origin.decode('utf-8') if real_image_code_origin else None
        con_redis.delete(img_key)

        # 验证手机号
        if (not real_image_code) or (image_text.upper() != real_image_code):
            raise forms.ValidationError("图片验证失败")

        # 检查是否在60s内有发送记录
        sms_flag_fmt = "sms_flag_{}".format(mobile_num).encode('utf-8')
        sms_flag = con_redis.get(sms_flag_fmt)
        if sms_flag:
            raise forms.ValidationError("获取手机短信验证码过于频繁")
