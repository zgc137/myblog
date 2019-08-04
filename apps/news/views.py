import json
from django.http import HttpResponseNotFound
from django.shortcuts import render
from django.views import View
from utils.res_code import Code, error_map
from . import models
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import logging
from utils.json_fun import to_json_data
from . import constants
# from haystack.views import SearchView as _SearchView

logger = logging.getLogger('django')

class IndexView(View):
    """
    tags:id,name
    """
    def get(self, request):
        """
        """
        tags = models.Tag.objects.only('id', 'name').filter(is_delete=False)
        hot_news = models.HotNews.objects.select_related('news').only('news__title', 'news__image_url',
                                                                      'news__id').filter(is_delete=False).order_by(
            'priority', '-news__clicks')[0:constants.SHOW_HOTNEWS_COUNT]
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
            tag_id = int(request.GET.get('tag_id', 0))

        except Exception as e:
            logger.error("标签错误：\n{}".format(e))
            tag_id = 0
        try:
            page = int(request.GET.get('page', 1))
        except Exception as e:
            logger.error("当前页数错误：\n{}".format(e))
            page = 1

        news_queryset = models.News.objects.select_related('tag', 'author'). \
            only('title', 'digest', 'image_url', 'update_time', 'tag__name', 'author__username')

        # if models.Tag.objects.only('id').filter(is_delete=False, id=tag_id).exists():
        #     news = news_queryset.filter(is_delete=False, tag_id=tag_id)
        # else:
        #     news = news_queryset.filter(is_delete=False)

        news = news_queryset.filter(is_delete=False, tag_id=tag_id) or \
               news_queryset.filter(is_delete=False)

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
                'id':n.id,
                'title': n.title,
                'digest': n.digest,
                'image_url': n.image_url,
                'tag_name': n.tag.name,
                'author': n.author.username,
                'update_time': n.update_time.strftime('%Y{y}%m{m}%d{d}').format(y='年', m='月', d='日'),

        })

        # 创建返回给前端的数据
        data = {
            'total_pages': paginator.num_pages,
            'news': news_info_list,
        }

        return to_json_data(data=data)


class NewsBanner(View):
    """
    url  /news/banners/
    前台不需要传参
    :param
    image__url
    news__id
    news__title

    """
    def get(self,request):
        banners = models.Banner.objects.select_related('news').\
                      only('image_url', 'news__id', 'news__title').\
            filter(is_delete=False)[0:constants.SHOW_BANNER_COUNT]

        # 序列化输出
        banners_info_list = []
        for b in banners:
            banners_info_list.append({
                'image_url': b.image_url,
                'news_id': b.news.id,
                'news_title': b.news.title,
            })

        # 创建返回给前端的数据
        data = {
            'banners': banners_info_list
        }

        return to_json_data(data=data)

class NewsDetailView(View):
    """
    新闻详情
    """
    def get(self,request, news_id):
        news = models.News.objects.select_related('tag', 'author').only('title', 'content', 'update_time', 'tag__name', 'author__username').filter(is_delete=False, id=news_id).first()

        if news:
            comments = models.Comments.objects.select_related('author','parent').only('content','update_time','author__username','parent__content','parent__author__username','parent__update_time').filter(is_delete=False,news_id=news_id)
            comments_list = []
            for comm in comments:
                comments_list.append(comm.to_dict_data())

            return render(request, 'news/news_detail.html',{'news':news,'comments_list':comments_list,})
        else:
            # raise Http404("<新闻{}>不存在😢".format(news_id))
            return HttpResponseNotFound("<新闻{}>不存在😢".format(news_id))

class NewsCommentView(View):
    """
 /news/<int:news_id>/comments/

    """

    def post(self, request, news_id):
        if not request.user.is_authenticated:
            return to_json_data(errno=Code.SESSIONERR, errmsg=error_map[Code.SESSIONERR])

        if not models.News.objects.only('id').filter(is_delete=False, id=news_id).exists():
            return to_json_data(errno=Code.PARAMERR, errmsg="新闻不存在！")

        # 从前端获取参数
        json_data = request.body
        # print(json_data)
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        # 将json转化为dict
        dict_data = json.loads(json_data.decode('utf8'))

        content = dict_data.get('content')
        if not dict_data.get('content'):
            return to_json_data(errno=Code.PARAMERR, errmsg="评论内容不能为空！")

        parent_id = dict_data.get('parent_id')
        try:
            if parent_id:
                parent_id = int(parent_id)
                if not models.Comments.objects.only('id'). filter(is_delete=False, id=parent_id, news_id=news_id).exists():
                    return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])

        except Exception as e:
            logging.info("前端传过来的parent_id异常：\n{}".format(e))
            return to_json_data(errno=Code.PARAMERR, errmsg="未知异常")

        # 保存到数据库
        new_content = models.Comments()
        new_content.content = content
        new_content.news_id = news_id
        new_content.author = request.user
        new_content.parent_id = parent_id if parent_id else None
        new_content.save()

        return to_json_data(data=new_content.to_dict_data())

# class SearchView(_SearchView):
#     # 模版文件
#     template = 'news/search.html'
#
#     # 重写响应方式，如果请求参数q为空，返回模型News的热门新闻数据，否则根据参数q搜索相关数据
#     def create_response(self):
#         kw = self.request.GET.get('q', '')
#         if not kw:
#             show_all = True
#             hot_news = models.HotNews.objects.select_related('news'). \
#                 only('news__title', 'news__image_url', 'news__id'). \
#                 filter(is_delete=False).order_by('priority', '-news__clicks')
#
#             paginator = Paginator(hot_news, settings.HAYSTACK_SEARCH_RESULTS_PER_PAGE)
#             try:
#                 page = paginator.page(int(self.request.GET.get('page', 1)))
#             except PageNotAnInteger:
#                 # 如果参数page的数据类型不是整型，则返回第一页数据
#                 page = paginator.page(1)
#             except EmptyPage:
#                 # 用户访问的页数大于实际页数，则返回最后一页的数据
#                 page = paginator.page(paginator.num_pages)
#             return render(self.request, self.template, locals())
#         else:
#             show_all = False
#             qs = super(SearchView, self).create_response()
#             return qs
