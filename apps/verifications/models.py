import logging


from django.views import View
from django_redis import get_redis_connection
from django.http import HttpResponse

from utils.captcha.captcha import captcha
# 安装图片验证码所需要的 Pillow 模块
# pip install Pillow
from . import constants

# 导入日志器
logger = logging.getLogger('django')


class ImageCode(View):
    """
    define image verification view
    # /image_codes/<uuid:image_code_id>/
    """

    # def get(self,request,image_code_id):
    def get(self,request,image_code_id):
        text, image = captcha.generate_captcha()

        # 确保settings.py文件中有配置redis CACHE
        # Redis原生指令参考 http://redisdoc.com/index.html
        # Redis python客户端 方法参考 http://redis-py.readthedocs.io/en/latest/#indices-and-tables
        con_redis = get_redis_connection(alias='verify_codes')
        img_key = "img_{}".format(image_code_id).encode('utf-8')
        # 将图片验证码的key和验证码文本保存到redis中，并设置过期时间
        con_redis.setex(img_key,constants.IMAGE_CODE_REDIS_EXPIRES, text)
        logger.info("Image code: {}".format(text))

        return HttpResponse(content=image, content_type="images/jpg")