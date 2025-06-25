#Напишите программу, которая проверит каждое число в списке на предмет того, является ли оно простым.

def f(a):
    str_a = str(a)
    l = len(str_a)

    s = 0
    for i in range(len(str_a)):
        num = int(str_a[i])
        print(num)
        s += num**l

    if s == a:
        return True
    return False

print(f(371))

