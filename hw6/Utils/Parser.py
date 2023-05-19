def parse_header(data: str):
    # Split the request into a list of strings
    lines = data.split("\r\n")
    # Initialize an empty dictionary to store the headers
    headers = {}
    # Iterate through the lines
    for line in lines:
        # Skip empty lines
        if line == "":
            break
        # Split the line into a key-value pair
        index = line.find(":", 1)
        if index != -1 and index + 2 < len(line):
            key, value = line[:index].strip(), line[index + 1 :].strip()
            headers[key.lower()] = value
    return headers


def parse_resource(resource: str):
    # Split resource into path and parameters
    resource = resource.split("?")
    if len(resource) == 2:
        path, parameters = resource
    else:
        return resource[0], {}

    # Split the parameters into list
    parameters = parameters.split("&")

    # Initialize an empty dictionary to store the params
    params = {}

    # Iterate through the parameters
    for para in parameters:
        # Split the para into a key-value pair
        para = para.split("=")
        if len(para) == 2:
            key, value = para
            params[key] = value
    return path, params


def parse_response(response_str: str):
    response = {
        "version": "",  # e.g. "HTTP/1.0"
        "status": "",  # e.g. "200 OK"
        "headers": {},  # e.g. {content-type: application/json}
        "body": "",  # e.g. "{'id': '123', 'key':'456'}"
    }
    # Split the request into a list of strings
    lines = response_str.split("\r\n")
    if len(lines) < 2:
        return None

    # Split the method, resource and version
    index = lines[0].find(" ")
    if index == -1 or index + 1 >= len(lines[0]):
        return None

    # Extract method and requested resource
    response["version"] = lines[0][:index]
    response["status"] = lines[0][index + 1 :]

    # Initialize an empty dictionary to store the headers
    headers = {}

    # Iterate through the lines
    for line in lines[1:]:
        # Skip empty lines
        if line == "":
            break
        # Split the line into a key-value pair
        index = line.find(":", 1)
        if index != -1 and index + 2 < len(line):
            key, value = line[:index].strip(), line[index + 1 :].strip()
            headers[key.lower()] = value
    response["headers"] = headers

    # Extract the body (if any)
    body = ""
    if "\r\n\r\n" in response_str:
        body = response_str.split("\r\n\r\n")[1]
    response["body"] = body
    return response


def parse_reqeust(request_str: str):
    request = {
        "method": "",  # e.g. "GET"
        "path": "",  # e.g. "/"
        "params": {},  # e.g. {'id': '123'}
        "version": "",  # e.g. "HTTP/1.0"
        "headers": {},  # e.g. {content-type: application/json}
        "body": "",  # e.g. "{'id': '123', 'key':'456'}"
    }
    # Split the request into a list of strings
    lines = request_str.split("\r\n")
    if len(lines) < 2:
        return None

    # Split the method, resource and version
    request_list = lines[0].split()
    if len(request_list) != 3:
        return None

    # Extract method and requested resource
    request["method"] = request_list[0]
    resource = request_list[1]
    request["version"] = request_list[2]

    request["path"], request["params"] = parse_resource(resource)

    # Initialize an empty dictionary to store the headers
    headers = {}
    # Iterate through the lines
    for line in lines[1:]:
        # Skip empty lines
        if line == "":
            break
        # Split the line into a key-value pair
        index = line.find(":", 1)
        if index != -1 and index + 2 < len(line):
            key, value = line[:index].strip(), line[index + 1 :].strip()
            headers[key.lower()] = value
    request["headers"] = headers

    # Extract the body (if any)
    body = ""
    if "\r\n\r\n" in request_str:
        body = request_str.split("\r\n\r\n")[1]
    request["body"] = body

    return request
