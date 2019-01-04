import csv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


if os.getenv("DATABASE_URL") == None:
   print("\n DATABASE URL not defined in env \n")

else:
   print(os.getenv("DATABASE_URL"))

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

#engine = create_engine("postgres://XXXXX:XXXXX@localhost:5432/project1")
#db = scoped_session(sessionmaker(bind=engine))


def main():
    f = open("books.csv")
    reader = csv.reader(f)
    for isbn, title, author, year in reader:
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                    {"isbn": isbn, "title": title, "author": author, "year": year })
        print(f"Added book with title {title} to table: books.")
    db.commit()

if __name__ == "__main__":
    main()
