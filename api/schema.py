import os
import psycopg2
import psycopg2.extras
#this bull
import logging
logger = logging.getLogger()
logger.setLevel(logging.WARNING)
from ariadne import QueryType, make_executable_schema
#Gae "mutation"
from ariadne import MutationType

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
    type Mutation {
        addBook(title: String!, author_id: ID!): Book
        updateBook(id: ID!, title: String, author_id: ID): Book
        deleteBook(id: ID!): Boolean
    }
"""

query = QueryType()
#Gae "mutation"
mutation = MutationType()

def _execute(query, params=None):
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(query, params)
    
    # Required to persist changes to Neon
    conn.commit() 
    
    try:
        result = cursor.fetchall()
    except psycopg2.ProgrammingError:
        result = None
        
    cursor.close()
    conn.close()
    return result

@query.field("authors")
def resolve_authors(*_):
    return _execute("SELECT * FROM authors")

@query.field("author")
def resolve_author(*_, id):
    result = _execute("SELECT * FROM authors WHERE author_id = %s", (id,))
    return result[0] if result else None

#This shit uses warning to fucking print the variable
@query.field("books")
def resolve_books(*_):
    logger.warning("Executing resolve_books...") 
    result = _execute("SELECT * FROM books")
    logger.warning(f"Data retrieved: {len(result)} kali dia ngulang/looping.")
    return result

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

#Mutation part - Create, Update, Delete (No Create, nde atas soale)
@mutation.field("addBook")
def resolve_add_book(*_, title, author_id):
    # Example using your _execute function to run an INSERT query
    query = "INSERT INTO books (title, author_id) VALUES (%s, %s) RETURNING *"
    result = _execute(query, (title, author_id))
    return result[0] if result else None

@mutation.field("updateBook")
def resolve_update_book(*_, id, title=None, author_id=None):
    fields = []
    params = []
    
    if title is not None:
        fields.append("title = %s")
        params.append(title)
    if author_id is not None:
        fields.append("author_id = %s")
        params.append(author_id)
        
    if not fields:
        logger.warning("Its all none you donkey")
        return None  # No fields provided to update
        
    params.append(id)
    sql = f"UPDATE books SET {', '.join(fields)} WHERE book_id = %s RETURNING *"
    result = _execute(sql, tuple(params))
    return result[0] if result else None

@mutation.field("deleteBook")
def resolve_delete_book(*_, id):
    sql = "DELETE FROM books WHERE book_id = %s RETURNING book_id"
    result = _execute(sql, (id,))
    return bool(result)  # Returns True if deleted, False if ID was not found

schema = make_executable_schema(type_defs, query, mutation)
