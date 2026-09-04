from http.server import BaseHTTPRequestHandler, HTTPServer

with open("static/index.html", "r", encoding="utf-8") as file:
    html = file.read()

with open("static/upload.html", "r", encoding="utf-8") as file:
    upload = file.read()

with open("static/images.html", "r", encoding="utf-8") as file:
    images = file.read()


class ImageServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()

            self.send_html(html)

        elif self.path == "/upload":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()

            self.send_html(upload)

        elif self.path == "/images/":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()

            self.send_html(images)

        elif self.path.startswith("/images/"):
            filename = self.path[len("/images/") :]
            extension = filename.split(".")[-1]
            content_types = {
                "jpg": "image/jpeg",
                "png": "image/png",
                "gif": "image/gif",
            }
            print(extension)
            print(filename)

            try:
                with open("images/" + filename, "rb") as file:
                    image_data = file.read()
            except FileNotFoundError:
                self.send_response(404)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write("Файл не знайдено".encode())
                return

            print(len(image_data))

            self.send_response(200)
            self.send_header("Content-type", content_types[extension])
            self.end_headers()
            self.wfile.write(image_data)

        else:
            self.send_response(404)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("Помилка 404: Сторінка не знайдена".encode())

    def send_html(self, html):
        return self.wfile.write(html.encode())

    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write("Готово".encode())

        content_type = self.headers["Content-Type"]
        content_length = int(self.headers["Content-Length"])
        data = self.rfile.read(content_length)

        data_start = data.find(b'"', data.find(b"filename=")) + 1
        data_end = data.find(b'"', data_start)

        filename = data[data_start:data_end].decode("utf-8")

        if "boundary=" in content_type:
            boundary = content_type.split("boundary=")[-1].strip()
            boundary = boundary.encode()

        image_start = data.find(b"\r\n\r\n") + 4
        image_end = data.find(b"\r\n" + boundary, image_start)

        image_data = data[image_start:image_end]

        with open("images/" + filename, "wb") as file:
            file.write(image_data)

        print(self.headers["Content-Type"])
        print(self.headers["Content-Length"])
        # print(data[::-1])
        # print(data[158:168])
        # print(boundary)
        # print(data.find(boundary))
        # print(data.find(boundary, 158))
        # print(len(image_data))
        # print(image_data[:10])
        # print(data.find(b"filename="))
        # print(data[88:200])
        # print(filename)
        # print(len(image_data))
        # print(image_data[:10])


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8000), ImageServerHandler)
    print("Server running on http://localhost:8000")
    server.serve_forever()
