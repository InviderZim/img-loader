import logging
import os
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import psycopg2

IMAGE_DIR = os.environ.get("IMAGE_DIR", "images")
LOG_FILE = os.environ.get("LOG_FILE", "logs/app.log")

with open("static/index.html", "r", encoding="utf-8") as file:
    html = file.read()

with open("static/upload.html", "r", encoding="utf-8") as file:
    upload = file.read()

with open("static/images.html", "r", encoding="utf-8") as file:
    images = file.read()

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="[%(asctime)s] Дія: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


def get_db_connection():
    return psycopg2.connect(
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"],
    )


def create_images_table():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id SERIAL PRIMARY KEY,
            filename TEXT NOT NULL,
            original_name TEXT NOT NULL,
            size INTEGER NOT NULL,
            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            file_type TEXT NOT NULL
        )
    """)

    connection.commit()
    cursor.close()
    connection.close()


def get_images(page):
    connection = get_db_connection()
    cursor = connection.cursor()

    offset = (page - 1) * 10

    cursor.execute(
        """
        SELECT id, filename, original_name, size, upload_time, file_type
        FROM images
        ORDER BY upload_time DESC
        LIMIT 10 OFFSET %s
        """,
        (offset,),
    )

    images = cursor.fetchall()

    cursor.close()
    connection.close()

    return images


def get_image_by_id(image_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT filename
        FROM images
        WHERE id = %s
        """,
        (image_id,),
    )

    image = cursor.fetchone()

    cursor.close()
    connection.close()

    return image


def get_images_count():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM images
        """)

    count = cursor.fetchone()[0]

    cursor.close()
    connection.close()

    return count


class ImageServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()

            self.send_html(html)
            logger.info("Відкрито головну сторінку")

        elif self.path == "/upload":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()

            self.send_html(upload)
            logger.info("Відкрито сторінку завантаження")

        elif self.path == "/images/" or self.path.startswith("/images/?"):
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)

            page = int(query_params.get("page", ["1"])[0])

            page = max(page, 1)

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()

            images_count = get_images_count()

            total_pages = (images_count + 9) // 10

            if total_pages == 0:
                total_pages = 1

            page = min(page, total_pages)

            images_data = get_images(page)

            gallery_html = ""

            if images_data:
                for image in images_data:
                    image_id = image[0]
                    filename = image[1]
                    original_name = image[2]
                    size = image[3]
                    upload_time = image[4]
                    file_type = image[5]

                    size_kb = round(size / 1024, 2)

                    gallery_html += '<div class="image-card">'

                    gallery_html += '<a href="/images/' + filename + '">'
                    gallery_html += '<img src="/images/' + filename + '">'
                    gallery_html += "</a>"

                    gallery_html += '<div class="image-info">'

                    gallery_html += '<div class="image-name">'
                    gallery_html += original_name
                    gallery_html += "</div>"

                    gallery_html += '<div class="image-meta">'

                    gallery_html += "<span>"
                    gallery_html += "<strong>Size:</strong>"
                    gallery_html += str(size_kb) + " KB"
                    gallery_html += "</span>"

                    gallery_html += "<span>"
                    gallery_html += "<strong>Uploaded:</strong>"
                    gallery_html += str(upload_time)
                    gallery_html += "</span>"

                    gallery_html += "<span>"
                    gallery_html += "<strong>Type:</strong>"
                    gallery_html += file_type
                    gallery_html += "</span>"

                    gallery_html += "</div>"
                    gallery_html += "</div>"

                    gallery_html += (
                        '<a class="delete-button" href="/delete/' + str(image_id) + '">'
                    )
                    gallery_html += "Delete"
                    gallery_html += "</a>"

                    gallery_html += "</div>"

            if not images_data:
                gallery_html = "<p>No uploaded images</p>"

            pagination_html = '<div class="pagination">'

            if page > 1:
                pagination_html += (
                    '<a href="/images/?page=' + str(page - 1) + '">Previous</a>'
                )
            else:
                pagination_html += '<span class="disabled">Previous</span>'

            pagination_html += (
                "<span>Page " + str(page) + " of " + str(total_pages) + "</span>"
            )

            if page < total_pages:
                pagination_html += (
                    '<a href="/images/?page=' + str(page + 1) + '">Next</a>'
                )
            else:
                pagination_html += '<span class="disabled">Next</span>'

            pagination_html += "</div>"

            gallery_html = images.replace(
                '<section class="gallery">\n\n        </section>',
                '<section class="gallery">\n\n        '
                + gallery_html
                + "\n\n        </section>\n\n        "
                + pagination_html,
            )

            self.send_html(gallery_html)
            logger.info("Відкрито галерею зображень")

        elif self.path.startswith("/images/"):
            filename = self.path[len("/images/") :]

            if os.path.basename(filename) != filename:
                self.send_response(400)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write("Недопустиме ім'я файлу".encode())
                return

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

            try:
                with open(IMAGE_DIR + "/" + filename, "rb") as file:
                    image_data = file.read()
            except FileNotFoundError:
                self.send_response(404)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write("Файл не знайдено".encode())
                logger.info(f"Файл не знайдено: {filename}")
                return

            self.send_response(200)
            self.send_header("Content-type", content_types[extension])
            self.end_headers()
            self.wfile.write(image_data)

        elif self.path.startswith("/delete/"):
            image_id = self.path[len("/delete/") :]

            try:
                image_id = int(image_id)
            except ValueError:
                self.send_response(400)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write("Недопустимий ID".encode())
                logger.info(f"Недопустимий ID для видалення: {image_id}")
                return

            image = get_image_by_id(image_id)

            if image is None:
                self.send_response(404)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write("Зображення не знайдено".encode())
                logger.info(f"Зображення не знайдено для видалення: {image_id}")
                return

            filename = image[0]
            file_path = IMAGE_DIR + "/" + filename

            try:
                os.remove(file_path)
            except FileNotFoundError:
                logger.info(f"Файл не знайдено під час видалення: {filename}")

            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                DELETE FROM images
                WHERE id = %s
                """,
                (image_id,),
            )

            connection.commit()
            cursor.close()
            connection.close()

            logger.info(f"Зображення видалено: {filename}")

            self.send_response(302)
            self.send_header("Location", "/images/")
            self.end_headers()

        else:
            self.send_response(404)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("Помилка 404: Сторінка не знайдена".encode())
            logger.info(f"Помилка 404: {self.path}")

    def send_html(self, html):
        return self.wfile.write(html.encode("utf-8"))

    def do_POST(self):
        content_type = self.headers["Content-Type"]
        content_length = int(self.headers["Content-Length"])
        data = self.rfile.read(content_length)

        data_start = data.find(b'"', data.find(b"filename=")) + 1
        data_end = data.find(b'"', data_start)

        filename = data[data_start:data_end].decode("utf-8")

        extension = filename.split(".")[-1].lower()

        if extension not in ("jpg", "png", "gif"):
            self.send_response(400)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("Недопустиме розширення файлу".encode())
            logger.info(f"Спроба завантаження недопустимого файлу: {filename}")
            return

        if "boundary=" in content_type:
            boundary = content_type.split("boundary=")[-1].strip()
            boundary = boundary.encode()

        image_start = data.find(b"\r\n\r\n") + 4
        image_end = data.find(b"\r\n" + boundary, image_start)

        image_data = data[image_start:image_end]

        unique_name = str(uuid.uuid4())
        unique_name = unique_name + "." + extension

        if len(image_data) > 5 * 1024 * 1024:
            self.send_response(400)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("Файл завеликий. Максимальний розмір — 5 МБ".encode())
            logger.info(f"Спроба завантаження завеликого файлу: {filename}")
            return

        file_path = IMAGE_DIR + "/" + unique_name

        with open(file_path, "wb") as file:
            file.write(image_data)

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO images (filename, original_name, size, file_type)
                VALUES (%s, %s, %s, %s)
                """,
                (unique_name, filename, len(image_data), extension),
            )

            connection.commit()

        except Exception:
            if "connection" in locals():
                connection.rollback()

            if "cursor" in locals():
                cursor.close()

            if "connection" in locals():
                connection.close()

            os.remove(file_path)

            logger.error(f"Помилка збереження в БД: {unique_name}")

            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("Помилка збереження зображення".encode())
            return

        else:
            cursor.close()
            connection.close()

        logger.info(f"Файл успішно завантажено: {unique_name}")

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()

        message = "File uploaded successfully\n"
        message += "/images/" + unique_name

        self.wfile.write(message.encode("utf-8"))


try:
    create_images_table()
    print("Database table is ready")
except psycopg2.Error as error:
    print(f"Database initialization failed: {error}")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8000), ImageServerHandler)
    print("Server running on port 8000")
    server.serve_forever()
