import socket
import json
import time

IP = '192.168.20.120'
PORT = 12345

if __name__ == '__main__':
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((IP, PORT))
    while True:
        json_data = {"action" : "start"}
        json_str = json.dumps(json_data)
        client.sendall(json_str.encode('utf-8'))

        json_str = client.recv(1024)
        json_data = json.loads(json_str.decode('utf-8'))
        print(json_data)

        start_time = time.time()
        while True:
            json_str = client.recv(1024)
            json_data = json.loads(json_str.decode('utf-8'))
            print(f"json: {json_data}")
            end_time = time.time()
            # if (end_time - start_time) * 1000 > 7654:
            # 如果是绿灯
            # if (json_data['datas'][0]['label'] == 'green'):
            #     print('end')
            #     json_data = {"action" : "stop"}
            #     json_str = json.dumps(json_data)
            #     client.sendall(json_str.encode('utf-8'))
            #     break


        # json_data = {"action" : "stop"}
        # json_str = json.dumps(json_data)
        # client.sendall(json_str.encode('utf-8'))

        json_str = client.recv(1024)
        json_data = json.loads(json_str.decode('utf-8'))
        print(json_data)

        # client.close()

