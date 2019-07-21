import json
import logging
import random
from . import forms
from users.models import User
from django_redis import get_redis_connection
from django.http import HttpResponse, JsonResponse
from utils.json_fun import to_json_data
from utils.yuntongxun.sms import CCP
from  utils.res_code import Code,error_map
from django.views import View
from utils.captcha.captcha import captcha
# 安装图片验证码所需要的 Pillow 模块
# pip install Pillow
from . import constants
import requests
# 导入日志器
logger = logging.getLogger('django')


class ImageCode(View):
    """
    define image verification view
    # /image_codes/<uuid:image_code_id>/
    """

    def get(self,request,image_code_id):
        text, image = captcha.generate_captcha()

        # 确保settings.py文件中有配置redis CACHE
        # Redis原生指令参考 http://redisdoc.com/index.html
        # Redis python客户端 方法参考 http://redis-py.readthedocs.io/en/latest/#indices-and-tables
        con_redis = get_redis_connection(alias='verify_codes')
        img_key = "img_{}".format(image_code_id).encode('utf-8')
        # 将图片验证码的key和验证码文本保存到redis中，并设置过期时间
        con_redis.setex(img_key, constants.IMAGE_CODE_REDIS_EXPIRES, text)
        logger.info("Image code: {}".format(text))

        return HttpResponse(content=image, content_type="images/jpg")


class CheckUsernameView(View):
    """
    Check whether the user exists
    GET usernames/(?P<username>\w{5,20})/
    """

    def get(self, request, username):
        # count = User.objects.get(username=username).count()
        data = {
            'username': username,
            'count': User.objects.filter(username=username).count(),
        }
        # return JsonResponse({'data':data})
        return to_json_data(data=data)



class CheckMobileView(View):
    """
    Check whether the user exists
    GET mobile/(?P<mobile>\1[3-9]\d{9}/
    """
    def get(self, request, mobile):
        # count = User.objects.filter(mobile=mobile).count()
        data = {
            'mobile': mobile,
            'count': User.objects.filter(mobile=mobile).count(),
        }
        # return JsonResponse({'data': data})
        return to_json_data(data=data)

class SmsCodesView(View):
    '''
    1、获取参数
    2、验证参数
    3、发送短信
    4、保存短信验证码
    5、返回给前端

    POST /sms_codes/
    -检查图片验证码是否正确
    -检查是否60S有记录
    -生成短信验证码
    -保存记录
    -发送短信
    '''
    #get value
    def post(self,request):
        json_str=request.body
        if not json_str:
            return to_json_data(errno = Code.PARAMERR,errmsg='参数为空，请重新输入')
        # json字符串转字典
        dict_data = json.loads(json_str.decode('utf8'))

        #2、校验参数 forms.py
        form = forms.CheckImgCodeForm(data=dict_data)
        if form.is_valid():
            # 获取手机号
            mobile = form.cleaned_data.get('mobile')
            # 3、
            # 创建短信验证码内容
            sms_num = "%06d" % random.randint(0, 999999)

        # 将短信验证码保存到数据库
        # 确保settings.py文件中有配置redis CACHE
        # Redis原生指令参考 http://redisdoc.com/index.html
        # Redis python客户端 方法参考 http://redis-py.readthedocs.io/en/latest/#indices-and-tables
        # 4、
            conn_redis = get_redis_connection(alias='verify_codes')

            # 创建一个在60s以内是否有发送短信记录的标记
            sms_flag_fmt = "sms_flag_{}".format(mobile).encode('utf8')
            # 创建保存短信验证码的标记key
            sms_text_fmt = "sms_{}".format(mobile).encode('utf8')
            pl = conn_redis.pipeline()

        # 此处设置为True会出现bug
            try:
                pl.setex(sms_flag_fmt, constants.SEND_SMS_CODE_INTERVAL, 1)
                pl.setex(sms_text_fmt, constants.SMS_CODE_REDIS_EXPIRES, sms_num)
                # 让管道通知redis执行命令
                pl.execute()
            except Exception as e:
                logger.debug("redis 执行出现异常：{}".format(e))
                return to_json_data(errno=Code.UNKOWNERR, errmsg=error_map[Code.UNKOWNERR])

            logger.info("SMS code: {}".format(sms_num))

            # 发送短语验证码
            try:
                result = CCP().send_template_sms(mobile,
                                                 [sms_num, constants.SMS_CODE_REDIS_EXPIRES],
                                                 constants.SMS_CODE_TEMP_ID)
            except Exception as e:
                logger.error("发送验证码短信[异常][ mobile: %s, message: %s ]" % (mobile, e))
                return to_json_data(errno=Code.SMSERROR, errmsg=error_map[Code.SMSERROR])
            else:
                if result == 0:
                    logger.info("发送验证码短信[正常][ mobile: %s sms_code: %s]" % (mobile, sms_num))
                    return to_json_data(errno=Code.OK, errmsg="短信验证码发送成功")
                else:
                    logger.warning("发送验证码短信[失败][ mobile: %s ]" % mobile)
                    return to_json_data(errno=Code.SMSFAIL, errmsg=error_map[Code.SMSFAIL])
