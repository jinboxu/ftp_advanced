import socket,json
import hashlib
import os, sys,time
import threading

client = socket.socket()
client.connect(('localhost', 6666))

class Ftp_client(object):
    def __init__(self):
        username = Ftp_client.login(self)
        client.send(b"get home path")
        self.home_path = client.recv(1024).decode()
        self.cur_path = self.home_path
        while True:
            if self.cur_path == self.home_path:
                view_path = '~'
            else:
                view_path = os.path.basename(self.cur_path)
            cmd = input('[%s@jinbo %s]$' %(username, view_path)).strip()
            if not cmd:continue
            self.cmd_list = cmd.split()
            print(self.cmd_list)
            if hasattr(self, self.cmd_list[0]):
                getattr(self, self.cmd_list[0])()
            else:
                print("cmd error")


    def login(self):
        while True:
            m = hashlib.md5()
            username = input('username:').strip()
            passwd = input('passwd:').strip()
            m.update(passwd.encode())
            passwd_secret = m.hexdigest()
            data = {'username':username, 'passwd_md5':passwd_secret}
            client.send(json.dumps(data).encode())
            data_result = client.recv(1024).decode()
            if data_result == "True":
                print("welcome!",username)
                return  username
            else:
                print("用户名或密码错误")

    def ls(self):
        if self.cmd_list == ["ls"]:
            client.send(json.dumps(self.cmd_list).encode())
            server_reponse = client.recv(1024).decode()
            print(server_reponse)
            cmd_res_size = int(server_reponse)
            client.send(b"ready to recv cmd res")

            received_size = 0
            received_data = b''
            while received_size < cmd_res_size:
                data = client.recv(1024)
                received_data += data
                received_size += len(data)
                print(cmd_res_size, received_size)
            else:
                print(received_data.decode())
        else:
            print("cmd error")


    def cd(self):   #注意'\' ,最好使用os.sep取代‘\\’，毕竟跨平台
        if len(self.cmd_list) != 2:
            print("cmd error")
            return
        if self.cmd_list == ['cd', '..']:
            cur_path = os.path.dirname(self.cur_path)
            if len(cur_path.split('\\')) >= 6:
                self.cur_path = cur_path
                client.send(json.dumps(self.cmd_list).encode())
                print('11')
                client.recv(1024)
                print('22')
            else:
                print("你只能在自己的家目录下活动")
        elif self.cmd_list == ['cd', '\\']:
            self.cur_path = self.home_path
            client.send(json.dumps(self.cmd_list).encode())
            client.recv(1024)
        else:
            change_dir = self.cmd_list[1]
            print(change_dir)
            if change_dir.startswith('.'):
                cur_path = os.path.join(self.cur_path, change_dir[2::])
            else:
                cur_path = self.cmd_list[1]
            print('cur_path', cur_path)
            print('home_path', self.home_path)
            if len(cur_path.split('\\')) >= 6 and cur_path.split('\\')[:6] == self.home_path.split('\\'):
                print('okok')
                self.cmd_list = ['cd', cur_path]
                print(self.cmd_list)
                client.send(json.dumps(self.cmd_list).encode())
                result = client.recv(1024).decode()
                if result == 'True':
                    self.cur_path = cur_path
                else:
                    print(result)
            else:
                print("用户只能在自己的家目录下活动")


    def pwd(self):
        print(self.cur_path)

    @staticmethod
    def view_bar(rate_num):
        r = '\r[%s%s]%d%%' % ("=" * rate_num, " " * (100 - rate_num), rate_num)  # \r 代表回车，也就是打印头归位，回到某一行的开头
        sys.stdout.write(r)
        sys.stdout.flush()


    def get(self):
        client.send( json.dumps(self.cmd_list).encode() )
        result = client.recv(1024).decode()
        file_list = self.cmd_list[1:]
        if result == "True":
            for file_name in file_list:
                server_response = client.recv(1024).decode()
                print('server response', server_response)
                client.send(b'ready to recv file')
                file_total_size = int(server_response)
                received_size = 0
                f = open(file_name, 'wb')
                m = hashlib.md5()

                # t =threading.Thread(target= Ftp_client.view_bar, args= (received_size, file_total_size,))
                # t.start()
                while received_size < file_total_size:
                    if file_total_size - received_size > 1024:
                        size = 1024
                    else:
                        size = file_total_size - received_size
                    data = client.recv(size)
                    received_size += len(data)
                    f.write(data)
                    m.update(data)
                    rate_num = int(received_size/file_total_size*100)
                    Ftp_client.view_bar(rate_num)

                else:
                    # t.join()
                    file_md5 = m.hexdigest()
                    print("\nfile recv done")
                    f.close()
                server_file_md5 = client.recv(1024).decode()
                client.send(b'get the md5')

                if file_md5 == server_file_md5:
                    print("文件%s MD5  一致" %file_name)
                else:
                    print("文件不一致！！")
                print(server_file_md5, file_md5)
            client.recv(1024)
        else:
            print("file %s is not exists" %result)


    def put(self):
        file_list = self.cmd_list[1:]
        for file_name in file_list:
            if not os.path.isfile(file_name):
                print("file %s is not exists" %file_name)
                return
        else:
            client.send( json.dumps(self.cmd_list).encode() )
        client.recv(1024)
        for file_name in file_list:
            file_size = os.stat(file_name).st_size
            client.send(str(file_size).encode())
            client.recv(1024)

            f = open(file_name, 'rb')
            m = hashlib.md5()
            put_size = 0
            for line in f:
                client.send(line)
                m.update(line)
                put_size += len(line)

                rate = put_size/file_size
                rate_num = int(rate*100)
                Ftp_client.view_bar(rate_num)
            f.close()
            file_md5 = m.hexdigest()
            server_file_md5 = client.recv(1024).decode()
            print("\nfile %s put over" %file_name)
            if file_md5 == server_file_md5:
                print("文件%s MD5  一致" %file_name)
            else:
                print("文件不一致！！")
            print(server_file_md5, file_md5)


if __name__ == '__main__':
    Ftp_client()
