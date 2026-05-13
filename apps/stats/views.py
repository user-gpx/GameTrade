from django.shortcuts import render
from django.shortcuts import HttpResponse

# Create your views here.

#查询字符串path('dash',stats_views.dash),
#localhost:8000/path?id=7&name= 
def dash(request):
    #id=request.GET.get('id')
    # name=request.GET.get('name')
    # if name==None:
    #     name='陌生人'
    return HttpResponse(f'你好')
#传参  path('index/<id>',stats_views.index)
#localhost:8000/path/id
def index(request,id):
    return HttpResponse(f'你好，你的id是{id}')
