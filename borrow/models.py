from django.db import models
from datetime import date

class book(models.Model):
    id = models.IntegerField(primary_key=True)
    book_name = models.CharField(max_length=40)
    available = models.IntegerField()

    def __str__(self):
        return str(self.id)   
    
class Student(models.Model):
    student_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    branch = models.CharField(max_length=30)
    contect = models.CharField(max_length=10)
    email = models.EmailField(max_length=300 ,unique=True)

    def __str__(self):
        return str(self.student_id)
    
from datetime import timedelta

class borrow_book(models.Model):
    book_id = models.ForeignKey(book, on_delete=models.CASCADE)
    student_id = models.ForeignKey(Student, on_delete=models.PROTECT)
    issue_date = models.DateField()
    return_date = models.DateField()
    
    def calculate_penalty(self):
       
        today = date.today()
        if self.return_date < today:
            late_days = (today - self.return_date).days
            penalty_amount = late_days * 1  # Adjust the rate here
            return penalty_amount
        return 0
    
class history(models.Model):
    book_id = models.ForeignKey(book, on_delete=models.CASCADE)
    student_id = models.ForeignKey(Student, on_delete=models.PROTECT)
    issue_date = models.DateField()
    return_date = models.DateField() 