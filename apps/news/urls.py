from django.urls import path
from . import views
app_name ='news'
#create your views here
urlpatterns = [
    # path('', views.index, name='index'),
    path('', views.IndexView.as_view(), name='index'),  # 将这条路由命名为index
    path('news/', views.NewsListView.as_view(), name='news_list'),
]