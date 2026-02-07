from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from langchain_experimental.sql import SQLDatabaseChain
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import PromptTemplate
from django.shortcuts import render, redirect
from .models import *
from datetime import date
from django.db.models import Count, Q
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from langchain_community.llms import Ollama


def log(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.info(request, "username or password is wrong")

    return render(request, "login.html")


def log_out(request):
    logout(request)
    return redirect('login')


@login_required(login_url="login")
def home(request):
    counts = borrow_book.objects.aggregate(
        filled_book_count=Count('book_id', filter=Q(book_id__isnull=False))
    )

    book_count = counts['filled_book_count']

    count2 = Student.objects.aggregate(
        student_count=Count('student_id', filter=Q(student_id__isnull=False))
    )
    student_count = count2['student_count']

    count3 = book.objects.aggregate(
        count_book=Count('id', filter=Q(id__isnull=False))
    )

    count_book = count3['count_book']

    dates = borrow_book.objects.all()
    today = date.today()
    d = 0
    for r_date in dates:
        if r_date.return_date < today:
            d += 1

    return render(request, "home.html", {'borrow_books': book_count, 'd': d, 'student_count': student_count, 'count_book': count_book})


@login_required(login_url="login")
def borrow(request):
    if request.method == 'POST':
        book_id = request.POST.get('book_id')
        student_id = request.POST.get('student_id')
        issue_date = request.POST.get('issue_date')
        return_date = request.POST.get('return_date')

        book_instance = book.objects.get(id=book_id)
        student_instance = Student.objects.get(student_id=student_id)
        borrow_instance = borrow_book.objects.create(
            book_id=book_instance,
            student_id=student_instance,
            issue_date=issue_date,
            return_date=return_date,
        )

        history.objects.create(
            book_id=book_instance,
            student_id=student_instance,
            issue_date=issue_date,
            return_date=return_date,
        )

        obj = book.objects.get(id=book_id)
        b = obj.available
        b -= 1
        obj.available = b
        obj.save()

        return redirect('borrow')

    obj1 = borrow_book.objects.all()
    today = date.today()

    return render(request, "borrow.html", {'borrows': obj1, 'today': today})


@login_required(login_url="login")
def student_info(request):
    obj1 = Student.objects.all()
    obj2 = book.objects.all()

    context = {'students': obj1, 'books': obj2}
    return render(request, "books.html", context)


def return_book(request, id):
    borrow = borrow_book.objects.get(id=id)
    book_obj = borrow.book_id
    borrow.delete()

    book_obj.available += 1
    book_obj.save()

    return redirect('borrow')


@login_required(login_url="login")
def re_issue(request, id):
    if request.method == "POST":
        issue_date = request.POST.get("issue_date")
        return_date = request.POST.get("return_date")

        id = id
        obj = borrow_book.objects.get(id=id)
        obj.issue_date = issue_date

        obj.return_date = return_date
        obj.save()
        return redirect('/borrow/')
    return render(request, "re_issue.html")


@login_required(login_url="login")
def add_book(request):
    obj2 = book.objects.all()

    if request.method == "POST":
        book_name = request.POST.get('book_name')
        available = request.POST.get('available')

        book.objects.create(book_name=book_name, available=available)

    return render(request, "add_book.html", {'books': obj2})


@login_required(login_url="login")
def add_student(request):
    if request.method == "POST":
        student_id = request.POST.get("student_id")
        name = request.POST.get("name")
        branch = request.POST.get("branch")
        contect = request.POST.get("contect")
        email = request.POST.get("email")

        Student.objects.create(
            student_id=student_id,
            name=name,
            branch=branch,
            contect=contect,
            email=email
        )
        return redirect("add_student")
    return render(request, "add_student.html")


@login_required(login_url="login")
def student(request, id):

    id = id
    obj = Student.objects.get(student_id=id)

    obj1 = history.objects.filter(student_id=id)

    context = {'student': obj, 'historys': obj1}

    return render(request, "student.html", context)


@login_required(login_url="login")
def b(request, id):

    id = id
    obj = book.objects.get(id=id)

    context = {'book': obj}

    return render(request, "book.html", context)


@csrf_exempt
def chat_bot(request):
    if request.method != 'POST':
        return JsonResponse(
            {"error": "Only POST method allowed"},
            status=405
        )

    try:
        data = json.loads(request.body)
        user_input = data.get("message")

        if not user_input:
            return JsonResponse(
                {"error": "Message is required"},
                status=400
            )

        llm = Ollama(model="mistral:7b",temperature=0)

        db = SQLDatabase.from_uri("sqlite:///db.sqlite3")

        chain = SQLDatabaseChain.from_llm(
            llm,
            db,
            verbose=True
        )

        response = chain.run(user_input)

        return JsonResponse({
            "reply": response
        })

    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Invalid JSON"},
            status=400
        )

    except Exception as e:
        return JsonResponse(
            {"error": str(e)},
            status=500
        )
