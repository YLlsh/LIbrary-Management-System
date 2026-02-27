from django.db.models import Sum
import string
import random
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

from django.contrib.admin.views.decorators import staff_member_required

from langchain_community.llms import Ollama


def log(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_staff:
                login(request, user)
                return redirect('home')
            else:
                login(request, user)
                return redirect('student_home')
        else:
            messages.info(request, "username or password is wrong")

    return render(request, "login.html")


@login_required(login_url="login")
def profile(request):
    user_data = user.objects.get(user=request.user)

    student = Student.objects.filter(
        student_id=user_data.student.student_id).first()

    return render(request, "profile.html", {"user_data": user_data, "contact": student.contect
                                            })

def change_password(request):
    if request.method == "POST":
        old = request.POST.get("old")
        new = request.POST.get("new")
        confirm = request.POST.get("confirm")

        u = request.user
        user = authenticate(request,username = u.username, password = old)
        if user is None:
            messages.error(request,"Old passwprd is incorrect")
            return redirect('profile')

        if new != confirm:
            messages.error(request,"New passwords do not match")
            return redirect('profile')
        u.set_password(new)
        u.save()

        messages.error(request,"Password changed successfully")

        return redirect('profile')
    
    return render(request,"profile.html")
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

    books = book.objects.all()
    students = Student.objects.all()
    obj1 = borrow_book.objects.all()
    today = date.today()

    return render(request, "borrow.html", {'borrows': obj1, 'today': today, "books": books, "students": students})


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
def edit_book(request, id):
    obj2 = book.objects.all()
    book_obj = book.objects.get(id=id)

    if request.method == "POST":
        book_name = request.POST.get('book_name')
        available = request.POST.get('available')

        book_obj.book_name = book_name
        book_obj.available = available
        book_obj.save()

        book.objects.create(book_name=book_name, available=available)

    return render(request, "add_book.html", {'book_obj': book_obj, "isedit": True, 'books': obj2})


@login_required(login_url="login")
def remove_book(request, id):
    book_obj = book.objects.get(id=id)
    book_obj.delete()

    return redirect("add_book")


def generate_studentId():
    length = 6
    studentId_str = ''.join(random.choices(string.digits, k=length))
    studentId = int(studentId_str)
    if Student.objects.filter(student_id=studentId).exists():
        return generate_studentId
    else:
        return studentId


@staff_member_required(login_url="login")
def add_student(request):
    if request.method == "POST":
        name = request.POST.get("name")
        branch = request.POST.get("branch")
        contect = request.POST.get("contect")
        email = request.POST.get("email")

        if Student.objects.filter(email=email).exists():
            messages.error(request, "Email is already taken")
            return redirect("add_student")

        if Student.objects.filter(contect=contect).exists():
            messages.error(request, "Contact number is already taken")
            return redirect("add_student")

        student = Student.objects.create(
            student_id=generate_studentId(),
            name=name,
            branch=branch,
            contect=contect,
            email=email
        )
        if name:
            name = name.split()[0]

        username_final = F'{name}{student.student_id}'
        u = User(username=username_final)
        u.email = email
        u.set_password(f"{u.username}")
        u.save()

        user.objects.create(
            user=u,
            student=student
        )

        return redirect("add_student")
    obj1 = Student.objects.all().order_by('-create_time')
    context = {'students': obj1}

    return render(request, "add_student.html", context)


@staff_member_required(login_url="login")
def edit_student(request, id):
    student_obj = Student.objects.get(student_id=id)
    if request.method == "POST":
        name = request.POST.get("name")
        branch = request.POST.get("branch")
        contect = request.POST.get("contect")
        email = request.POST.get("email")

        if Student.objects.filter(email=email).exclude(student_id=id).exists():
            messages.error(request, "Email is already taken")
            return redirect("add_student")

        if Student.objects.filter(contect=contect).exclude(student_id=id).exists():
            messages.error(request, "Contact number is already taken")
            return redirect("add_student")

        student_obj.name = name
        student_obj.branch = branch
        student_obj.contect = contect
        student_obj.email = email
        student_obj.save()

        messages.error(request, "Student Edit Successfully")

        return redirect("add_student")

    obj1 = Student.objects.all().order_by('-create_time')
    context = {'students': obj1, 'student_obj': student_obj, "isedit": True}

    return render(request, "add_student.html", context)


@staff_member_required(login_url="login")
def remove_student(request, id):
    student_obj = Student.objects.get(student_id=id)
    student_obj.delete()

    messages.error(request, "Student is deleted successfully")

    return redirect("add_student")


@login_required(login_url="login")
def student(request, id):

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


@login_required(login_url="login")
def over_due(request):
    today = date.today()
    books = borrow_book.objects.filter(return_date__lt=today)

    return render(request, 'borrow_list.html', {"borrows": books, "today": today})


@login_required(login_url="login")
def all_borrow(request):
    today = date.today()
    if request.user.is_staff:
        books = borrow_book.objects.all()
    else:
        u = user.objects.filter(user = request.user).first()
        books = borrow_book.objects.filter(student_id = u.student.student_id)

    return render(request, 'borrow_list.html', {"borrows": books, "today": today})


# def all_borrow(request):
#     today = date.today()
#     books = borrow_book.objects.all()

#     return render(request, 'borrow_list.html', {"borrows": books, "today": today})


@login_required(login_url="login")
def hostory(request):

    if request.user.is_staff:
        obj1 = history.objects.all()
        context = {'historys': obj1}
    else:
        u = user.objects.filter(user=request.user).first()

        obj = Student.objects.get(student_id=u.student.student_id)

        obj1 = history.objects.filter(student_id=u.student.student_id)

        context = {'student': obj, 'historys': obj1}

    return render(request, "student.html", context)


@login_required(login_url="login")
def over_due(request):
    today = date.today()
    # u = User.objects.filter(user=request.user.id).first()
    user_obj = user.objects.filter(user=request.user).first()

    if request.user.is_staff:
        books = borrow_book.objects.filter(return_date__lt=today)
    else:
        books = borrow_book.objects.filter(
            Q(return_date__lt=today) & Q(student_id=user_obj.student))
        # some issue in this code return all books of user

    return render(request, 'borrow_list.html', {"borrows": books, "today": today})


@login_required(login_url="login")
def student_home(request):

    today = date.today()
    tomorrow = today + timedelta(days=1)

    user_obj = user.objects.filter(user=request.user).first()

    borrow_books = borrow_book.objects.filter(student_id=user_obj.student)

    tomorrow_return = borrow_books.filter(return_date=tomorrow).count()

    total_penalty = 0
    for i in borrow_books:
        total_penalty += i.calculate_penalty()

    current_borrow = borrow_books.count()
    overdue_count = borrow_books.filter(return_date__lt=today).count()

    history_count = history.objects.filter(student_id=user_obj.student).count()

    context = {
        "tomorrow_return": tomorrow_return,
        "total_penalty": total_penalty,
        "current_borrow": current_borrow,
        "overdue_count": overdue_count,
        "history_count":history_count
    }

    return render(request, "home_student.html", context)


def tomorrow_return(request):
    today = date.today()
    tomorrow = today + timedelta(days=1)

    u = user.objects.filter(user=request.user).first()

    books = borrow_book.objects.filter(
        Q(student_id=u.student.student_id) & Q(return_date=tomorrow))

    return render(request, 'borrow_list.html', {"borrows": books, "today": today})


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

        llm = Ollama(model="mistral:7b", temperature=0)

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
