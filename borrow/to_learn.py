import random
import string
# from models import Student

def generate_studentId():
    length = 3
    studentId = ''.join(random.choices(string.ascii_uppercase,k=length)+random.choices(string.digits, k=length))

    # if Student.objects.filter(student_id = studentId).exists():
    #     return generate_studentId
    # else:
    return studentId
   
print(generate_studentId())