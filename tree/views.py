from django.shortcuts import render
from demon.db import DataBase


def index(request):
    file_system = DataBase().get_tree("/home/plevytskyi/test_scan")
    context = {'file_system': file_system}
    return render(request, 'tree/index.html', context)
