from http.server import BaseHTTPRequestHandler, HTTPServer
import re
import redis
from http.cookies import SimpleCookie
import uuid
from urllib.parse import parse_qsl, urlparse

mappings = {(r"^/books/(?P<book_id>\d+)$", "get_books"),
            (r"^/books/(?P<book_id>\d+)$", "get_books"),
            (r"^/$", "index"),
            (r"^/search", "search")}

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

    def url_mapping_response(self):
        for pattern, method in mappings:
            match = self.get_params(pattern, self.path)
            if match is not None:
                md = getattr(self, method)
                md(**match)
                return

        self.send_response(404)
        # self.send_header("Content-Type", "text/html")
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


    def get_recomendation(self,session_id, book_id):
        books=r.lrange(f"session:{session_id}",0,-1)
        print(session_id, books)

        books_read = {book.decode('utf-8').split(':')[1] for book in books}

        all_books = {'1','2','3','4','5'}

        books_to_recommend = all_books-books_read
        if len(books_read)>=3:
            if books_to_recommend:
                return f"Te recomendamos leer el libro : {books_to_recommend.pop()}"
            else: 
                return "Ya has leido todos los libros"
        else:
            return "Lee el menos tres libros para obtener recomendaciones"


    def get_by_search(self):
        if self.query_data and 'q' in self.query_data:
            # Buscar libros que coincidan con la consulta
            booksInter = r.sinter(self.query_data['q'].split(' '))
            lista = []
        
            # Decodificar los resultados y agregarlos a la lista
            for b in booksInter:
                y = b.decode()
                lista.append(y)
        
            # Si no se encontraron libros, redirigir a get_index
            if not lista:
                self.index()
            else:
                # Si se encontraron libros, procesar cada uno
                for book in lista:
                    self.get_book(book)

        # Configurar la respuesta HTTP para indicar éxito
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()



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

