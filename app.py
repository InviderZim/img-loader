import uuid
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

            if extension not in ("jpg", "png", "gif"):
                self.send_response(400)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write("Недопустиме розширення файлу".encode())
                return

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

        content_type = self.headers["Content-Type"]
        content_length = int(self.headers["Content-Length"])
        data = self.rfile.read(content_length)

        data_start = data.find(b'"', data.find(b"filename=")) + 1
        data_end = data.find(b'"', data_start)

        filename = data[data_start:data_end].decode("utf-8")

        extension = filename.split(".")[-1]
        if extension not in ("jpg", "png", "gif"):
            self.send_response(400)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("Недопустиме розширення файлу".encode())
            return

        if "boundary=" in content_type:
            boundary = content_type.split("boundary=")[-1].strip()
            boundary = boundary.encode()

        image_start = data.find(b"\r\n\r\n") + 4
        image_end = data.find(b"\r\n" + boundary, image_start)

        image_data = data[image_start:image_end]

        unique_name = str(uuid.uuid4())
        unique_name = unique_name + "." + extension
        print(unique_name)

        if len(image_data) > 5 * 1024 * 1024:
            self.send_response(400)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("Файл завеликий. Максимальний розмір — 5 МБ".encode())
            return

        with open("images/" + unique_name, "wb") as file:
            file.write(image_data)

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        message = "Файл успішно завантажено\n"
        message += "http://localhost:8000/images/" + unique_name

        self.wfile.write(message.encode("utf-8"))

        print(self.headers["Content-Type"])
        print(self.headers["Content-Length"])


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8000), ImageServerHandler)
    print("Server running on http://localhost:8000")
    server.serve_forever()
