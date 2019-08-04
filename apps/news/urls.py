from django.urls import path
from . import views
app_name ='news'
#create your views here
urlpatterns = [
    # path('', views.index, name='index'),
    path('', views.IndexView.as_view(), name='index'),  # 将这条路由命名为index
    path('news/', views.NewsListView.as_view(), name='news_list'),
    path('news/banners/', views.NewsBanner.as_view(), name='news_banner'),
    path('news/<int:news_id>/', views.NewsDetailView.as_view(), name='news_detail'),
    path('news/<int:news_id>/comments/', views.NewsCommentView.as_view(), name='news_comment'),
    # path('search/', views.SearchView(), name='search'),

]