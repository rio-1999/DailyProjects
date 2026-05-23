
s = "abc"
print(id(s))
s = s + "d"        
print(s)
print(id(s))

lst = [1, 2, 3]
print(id(lst))
lst.append(4)
print(id(lst))


def add_item(item, basket = []):
    basket.append(item)
    print(id(basket))
    return basket


print(add_item("りんご"))
print(add_item("みかん"))
print(add_item("ぶどう"))

