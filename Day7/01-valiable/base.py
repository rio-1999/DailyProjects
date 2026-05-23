x = 42
y = 42
z = y


print(id(x), id(y), id(x) == id(y), id(z))

x = 100

print(x, y, z)

print(id(x), id(y), id(x) == id(y), id(z))