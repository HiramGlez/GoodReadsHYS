from http.server import BaseHTTPRequestHandler, HTTPServer
import re
import redis
from http.cookies import SimpleCookie
import uuid
from urllib.parse import parse_qsl, urlparse
import json
import random

mappings = {(r"^/books/(?P<book_id>\d+)$", "get_books"),
            (r"^/books/(?P<book_id>\d+)$", "get_books"),
            (r"^/$", "index"),
            (r"^/buscar$", "buscarLibro")
            (r"^/recomendar$", "recomendarLibro")}

r = redis.StrictRedis(host="localhost", port=6379, db=0)

class WebRequestHandler(BaseHTTPRequestHandler):

    @property
    def url(self):
        return urlparse(self.path)

    @property 
    def query_data(self):
        return dict(parse_qsl(self.url.query))

    def search(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        index_page = f"<h1> {self.query_data['q'].split()} </h1>".encode("utf-8")
        self.wfile.write(index_page)

    def cookies(self):
        return SimpleCookie(self.headers.get("Cookie"))

    def get_session(self):
        cookies = self.cookies()
        session_id = None
        if not cookies:
            session_id = uuid.uuid4()
        else:
            session_id = cookies["session_id"].value
        return session_id

    def write_session_cookie(self, session_id):
        cookies = SimpleCookie()
        cookies["session_id"] = session_id
        cookies["session_id"]["max-age"] = 1000
        self.send_header("Set-Cookie", cookies.output(header=""))

    def do_GET(self):
        self.url_mapping_response()

        if self.path.startswith('/buscarLibro'):
            query = self.path.split('=')[1] 
            book_info = self.buscar_libro(query)
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(book_info.encode())

        elif self.path.startswith('/recomendarLibro'):
            book_info = self.recomendar_libro()
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(book_info.encode())

        else:
            self.send_error(404, 'File not found')

            if self.path == '/recomendarLibro':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            # Lista de libros disponibles
            libros = [
                {"id": 1, "nombre": "La vida secreta de la mente"},
                {"id": 2, "nombre": "Más allá de la niebla"}
                {"id": 3, "nombre": "La chica del tren"}
                {"id": 4, "nombre": "El libro negro del programador"}
                {"id": 5, "nombre": "La cabaña"}
                {"id": 6, "nombre": "El código del héroe"}
            ]

            
            libro_recomendado = random.choice(libros)

            
            response_data = json.dumps({"bookName": libro_recomendado["nombre"], "bookId": libro_recomendado["id"]})
            self.wfile.write(response_data.encode())

    def url_mapping_response(self):
        for pattern, method in mappings:
            match = self.get_params(pattern, self.path)
            if match is not None:
                md = getattr(self, method)
                md(**match)
                return

        self.send_response(404)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        error = f"<h1> Not found </h1>".encode("utf-8")
        self.wfile.write(error)

    def get_params(self, pattern, path):
        match = re.match(pattern, path)
        if match:
            return match.groupdict()

    def get_books(self, book_id):
        session_id = self.get_session()
        r.lpush(f"session: {session_id}", f"book: {book_id}")
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.write_session_cookie(session_id)
        self.end_headers()
        book_info = r.get(f"book: {book_id}") or "<h1> No existe el libro </h1>".encode("utf-8")
        self.wfile.write(book_info)
        self.wfile.write(f"session: {session_id}".encode("utf-8"))
        book_list = r.lrange(f"session: {session_id}", 0, 1)
        for book in book_list:
            self.wfile.write(f" book: {book}".encode("utf-8"))


    def buscarLibro(self, query):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()

        
        if query == "La vida secreta de la mente":
            book_info = """
            <h2>La vida secreta de la mente</h2>
            <p>Mariano Sigman</p>
            <p>La vida secreta de la mente es un viaje especular que recorre el cerebro y el pensamiento: se trata de descubrir nuestra mente para entendernos hasta en los más pequeños rincones que componen lo que somos, cómo forjamos las ideas en los primeros días de vida, cómo damos forma a las decisiones que nos constituyen, cómo soñamos y cómo imaginamos, por qué sentimos ciertas emociones hacia los demás, cómo los demás influyen en nosotros, y cómo el cerebro se transforma y, con él, lo que somos.</p>
            <div class="book-container">
                <img class="book-image" src="https://m.media-amazon.com/images/I/41rUpuKsp4L.jpg" alt="La vida secreta de la mente">
            </div>
            """
        else:
            book_info = "<h1>No se encontró el libro</h1>"

        self.wfile.write(book_info.encode("utf-8"))
    

    def recomendarLibro(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()

         
        book_info = """
        <h2>La vida secreta de la mente</h2>
        <p>Mariano Sigman</p>
        <p>La vida secreta de la mente es un viaje especular que recorre el cerebro y el pensamiento: se trata de descubrir nuestra mente para entendernos hasta en los más pequeños rincones que componen lo que somos, cómo forjamos las ideas en los primeros días de vida, cómo damos forma a las decisiones que nos constituyen, cómo soñamos y cómo imaginamos, por qué sentimos ciertas emociones hacia los demás, cómo los demás influyen en nosotros, y cómo el cerebro se transforma y, con él, lo que somos.</p>
        <div class="book-container">
            <img class="book-image" src="https://m.media-amazon.com/images/I/41rUpuKsp4L.jpg" alt="La vida secreta de la mente">
        </div>
        """
        
        self.wfile.write(book_info.encode("utf-8"))


        def get_query_param(self, param_name):
        query_params = self.path.split('?')[1]
        params = query_params.split('&')
        for param in params:
            name, value = param.split('=')
            if name == param_name:
                return value
        return None
        


    def index(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        index_page = """
        <h1> Bienvenidos a los libros </h1>
        <form action="/search" method="GET">
            <label for="q">Search</label>
            <input type="text" name="q"/>
            <input type="submit" value="Buscar Libros"/>
        </form>
        """.encode("utf-8")
        self.wfile.write(index_page)

if __name__ == "__main__":
    print("Server starting...")
    server = HTTPServer(("0.0.0.0", 8000), WebRequestHandler)
    server.serve_forever()

