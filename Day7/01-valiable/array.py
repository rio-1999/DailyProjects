a = [1,2,3]
b = a

print(id(a), id(b), id(a) == id(b))

a.append(4)
print("a =", a)
print("b =", b)

print(id(a), id(b), id(a) == id(b))