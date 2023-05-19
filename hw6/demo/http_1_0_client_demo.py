from my import http_1_0_client
import json
import os
import glob
import xml.etree.ElementTree as ET
        
if __name__ == '__main__':
    client = http_1_0_client.HTTPClient()

    target_path = "../../target"
    response = client.get(url=f"127.0.0.1:8080/")
    file_list = []
    if response and response.headers['content-type'] == 'text/html':
        root = ET.fromstring(response.body.decode())
        links = root.findall('.//a')
        file_list = []
        for link in links:
            file_list.append(link.text) 

    for file in glob.glob(os.path.join(target_path, '*.txt')):
        os.remove(file)

    for file in file_list:
        response = client.get(f"127.0.0.1:8080/static/{file}", stream=True)
        file_path = f"{target_path}/{file}"
        if response:
            print(f"{file_path} begin")
            with open(file_path, "wb") as f:
                while True:
                    content = response.get_stream_content()
                    if content is None:
                        break
                    f.write(content)
            print(f"{file_path} end")
        else:
            print("no response")