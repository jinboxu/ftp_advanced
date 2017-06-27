import json, os
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print('base-dir: %s' %base_dir)
# username = "wang"
# home_dir = os.path.join(base_dir, 'home', username)
# print(home_dir)

while True:
    while True:
        username = input("username: ").strip()
        if username:
            break
    while True:
        passwd = input("passwd: ").strip()
        if passwd:
            break
    while True:
        home_size = input("磁盘配额大小：").strip()
        if home_size.isdigit():
            break
    user_data = {"username":username, "passwd":passwd, "home_size":home_size}
    with open(username , 'w', encoding='utf-8') as f:
        json.dump(user_data, f)
    home_dir = os.path.join(base_dir, 'home', username)
    print(type(home_dir))
    os.mkdir(home_dir)
    os.mkdir(os.path.join(home_dir, 'test1'))
    os.mkdir(os.path.join(home_dir, 'test2'))
