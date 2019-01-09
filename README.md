# CS50  Web programming Project 1

This submission consists of a website using FLASK, according to requirements specified in:
https://docs.cs50.net/web/2018/x/projects/1/project1.html

Persistent information is stored in an internal Postgres DB with three tables:
- Users
- Books
- Review

The tables have been created as follows:
- Table users:
   CREATE TABLE users (
         id SERIAL PRIMARY KEY,
         username VARCHAR(30) NOT NULL,
         password VARCHAR(30) NOT NULL
     );
   ALTER TABLE users ADD CONSTRAINT unique_usernames UNIQUE (username);

- Table books:
   CREATE TABLE books (
      id SERIAL PRIMARY KEY,
      isbn VARCHAR NOT NULL,
      title VARCHAR NOT NULL,
      author VARCHAR NOT NULL,
      year INTEGER NOT NULL
  );

- Table review:
  CREATE TABLE review (
      id SERIAL PRIMARY KEY,
      rating INTEGER NOT NULL,
      comment VARCHAR,
      username_id INTEGER REFERENCES users,
      isbn_id INTEGER REFERENCES books
  );

The website provides the following functions:
- Register username and password (username must be unique, enforced in the DB)
- Login and Logout
- When logged in ability to use a Search function (/search), which provides a combination of results (/results)
- Leave a review
- An API function (/api<isbn>)
