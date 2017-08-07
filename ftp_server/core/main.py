import socketserver
import json, os, hashlib

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
conf_path = base_dir


class MyHandle( socketserver.BaseRequestHandler ):
    def handle(self):
        username = MyHandle.login(self)
        self.home_dir = os.path.join(base_dir, 'home', username)
        print(self.home_dir)
        os.chdir(self.home_dir)
        self.request.recv(1024)
        self.cur_path = os.getcwd()
        self.request.send(self.cur_path.encode())   #将当前工作路径发给客户端
        while True:
            try:
                cmd = self.request.recv(1024).decode()
                self.cmd_list = json.loads(cmd)
                print(self.cmd_list)
                getattr(self, self.cmd_list[0])()
            except ConnectionResetError:
                print('客户端已断开')
                self.request.close()


        # while True:
        #     cmd = self.request.recv(1024).decode()
        #     if not cmd:
        #         print("客户端已断开")
        #         self.request.close()
        #     self.cmd_list = json.loads(cmd)
        #     print(self.cmd_list)
        #     getattr(self, self.cmd_list[0])()

    def login(self):
        while True:
            try:
                username_passwdMd = json.loads(self.request.recv(1024).decode())
                print(username_passwdMd)
                username = username_passwdMd["username"]
                passwdMd = username_passwdMd["passwd_md5"]
                user_path = os.path.join(base_dir, "conf", username)
                print(user_path)
                if os.path.isfile(user_path):
                    user_data = json.load(open(user_path, 'r'))
                    passwd = user_data["passwd"]
                    m = hashlib.md5()
                    m.update(passwd.encode())
                    my_passwd_md = m.hexdigest()
                    if my_passwd_md == passwdMd:
                        self.request.send(b"True")
                        return username
                    else:
                        self.request.send(b"False")
                else:
                    self.request.send(b"False")

            except ConnectionResetError as e:
                print("ConnectResetError:", e)

    def cd(self):
        if self.cmd_list == ['cd', '\\']:       #此处不需要判断用户是否在家目录下，因为在客户端已经判断过了
            self.cur_path = self.home_dir
            self.request.send(b'get it')
        elif self.cmd_list == ['cd', '..']:
            self.cur_path = os.path.dirname(self.cur_path)
            self.request.send(b'get it')
        else:
            cur_path = self.cmd_list[1]
            print(cur_path)
            print(self.home_dir)
            if os.path.isdir(cur_path):
                self.cur_path = cur_path
                self.request.send(b'True')
            else:
                self.request.send(b"dir is not exists")


    def ls(self):
        res = str(os.listdir(self.cur_path))
        self.request.send( str(len(res)).encode() )
        self.request.recv(1024)
        self.request.send(res.encode())

    def get(self):
        file_list = self.cmd_list[1:]
        print('cur_path',self.cur_path)
        for file_name in file_list:     #判断是否有文件不存在
            file_path = os.path.join(self.cur_path, file_name)
            if not os.path.isfile(file_path):
                print("file %s is not exists" %file_path)
                self.request.send(file_name.encode())
                return
        else:
            self.request.send(b"True")
        for file_name in file_list:    #依次发送各个文件
            file_path = os.path.join(self.cur_path, file_name)
            f = open(file_path, 'rb')
            m = hashlib.md5()
            file_size = os.stat(file_path).st_size
            self.request.send( str(file_size).encode() )
            self.request.recv(1024)
            for line in f:
                m.update(line)
                self.request.send(line)
            print("file md5",m.hexdigest())
            f.close()
            self.request.send(m.hexdigest().encode())
            self.request.recv(1024)    #循环发送文件，在最后增加一次交互防止粘包的发生(MD5和size)
        self.request.send(b'files send over')




    def put(self):
        self.request.send(b'ready to get files')
        file_list = self.cmd_list[1:]
        for file_name in file_list:
            file_size = int(self.request.recv(1024).decode())
            self.request.send(b'ready')

            f = open(file_name, 'wb')
            m = hashlib.md5()
            received_size = 0
            while received_size < file_size:
                data = self.request.recv(1024)
                f.write(data)
                received_size += len(data)
                m.update(data)
            file_md5 = m.hexdigest()
            self.request.send(file_md5.encode())



# if __name__ == "__main__":
#     server = socketserver.ThreadingTCPServer(('localhost', 6666), MyHandle)
#     server.serve_forever()

def run():
    server = socketserver.ThreadingTCPServer(('localhost', 6666), MyHandle)
    server.serve_forever()
