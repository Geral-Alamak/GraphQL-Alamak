import os
import psycopg2
import psycopg2.extras
from ariadne import QueryType, make_executable_schema, snake_case_fallback_resolvers

type_defs = """
    type Author {
        author_id: ID!
        name: String!
    }
    type Book {
        book_id: ID!
        title: String!
        author_id: Int!
    }
    type Review {
        review_id: ID!
        book_id: Int!
        rating: Int!
        review_text: String
    }
    type Query {
        authors: [Author!]!
        author(id: ID!): Author
        books: [Book!]!
        book(id: ID!): Book
        reviews: [Review!]!
        review(id: ID!): Review
    }
"""

query = QueryType()

def _execute(sql, params=()):
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, params)
        result = cur.fetchall()
        cur.close()
        conn.close()
        return result
    except Exception:
        return []

@query.field("authors")
def resolve_authors(*_):
    return _execute("SELECT * FROM authors")

@query.field("author")
def resolve_author(*_, id):
    result = _execute("SELECT * FROM authors WHERE author_id = %s", (id,))
    return result[0] if result else None

@query.field("books")
def resolve_books(*_):
    return _execute("SELECT * FROM books")

@query.field("book")
def resolve_book(*_, id):
    result = _execute("SELECT * FROM books WHERE book_id = %s", (id,))
    return result[0] if result else None

@query.field("reviews")
def resolve_reviews(*_):
    return _execute("SELECT * FROM reviews")

@query.field("review")
def resolve_review(*_, id):
    result = _execute("SELECT * FROM reviews WHERE review_id = %s", (id,))
    return result[0] if result else None

schema = make_executable_schema(type_defs, query, snake_case_fallback_resolvers)
