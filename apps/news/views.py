from django.shortcuts import render
from django.views import View
from . import models
from django.core.paginator import Paginator,EmptyPage
import logging
from utils.json_fun import to_json_data
from . import constants

logger = logging.getLogger('django')

class IndexView(View):
    """
    tags:id,name
    """
    def get(self, request):
        """
        """
        tags = models.Tag.objects.only('id', 'name').filter(is_delete=False)

        return render(request, 'news/index.html', locals())

class NewsListView(View):
    '''
    1,获取参数
    2,校验参数
    3,数据库拿数据
    4,分页
    5，返回给前端
    ：param 必传参数
    tag_id
    page
    '''
    def get(self,request):

        try:
            tag_id = request.GET.get('tag_id')
        except Exception as e:
            logger.error("标题错误：\n{}".format(e))
            tag_id = 0

        #page
        try:
            page = int(request.GET.get('page',1))
        except Exception as e:
            logger.error("当前页数错误：\n{}".format(e))
            page = 1

        #数据库取数据
        # #select_related 一次性查出news关联的对象
        news_queryset = models.News.objects.select_related('tag', 'author'). \
            only('title', 'digest', 'image_url', 'update_time', 'tag__name', 'author__username')

        # if models.Tag.objects.only('id').filter(is_delete=False, id=tag_id).exists():
        # news = news_queryset.filter(is_delete=False, tag_id=tag_id)
        # else:
        # news = news_queryset.filter(is_delete=False)

        news = news_queryset.filter(is_delete=False, tag_id=tag_id) or  news_queryset.filter(is_delete=False)

        paginator = Paginator(news, constants.PER_PAGE_NEWS_COUNT)
        try:
            news_info = paginator.page(page)
        except EmptyPage:
            # 若用户访问的页数大于实际页数，则返回最后一页数据
            logging.info("用户访问的页数大于总页数。")
            news_info = paginator.page(paginator.num_pages)

        # 序列化输出
        news_info_list = []
        for n in news_info:
            news_info_list.append({
                'title': n.title,
                'digest': n.digest,
                'image_url': n.image_url,
                'tag_name': n.tag.name,
                'author': n.author.username,
                # 'update_time': n.update_time.strftime('%Y年%m月%d日 %H:%M'),
                'update_time': n.update_time.strftime('%Y{y}%m{m}%d{d}').format(y='年', m='月', d='日')

            })

        # 创建返回给前端的数据
        data = {
            'total_pages': paginator.num_pages,
            'news': news_info_list
        }

        return to_json_data(data=data)




