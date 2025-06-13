# CodeLeap Selection Process - Backend

This is a backend application built with Django REST Framework using ModelViewSet for clean and consistent API development. The project follows the Conventional Commits specification and includes a complete suite of unit tests.

---

## Features

* **User Authentication**: Users can register and obtain JWT tokens for authentication.
* **Post Management**: Authenticated users can create, retrieve, update, and delete their own posts.
* **Post Interactions**:
    * **Likes**: Users can like and unlike posts.
    * **Shares (Reposts)**: Users can share/repost content from other users.
    * **Comments**: Users can comment on posts, and modify or delete their own comments.
* **Trending Posts**: An endpoint to view posts ordered by the number of likes.
* **User Profiles**: View posts created by a specific user and posts shared by a specific user.
* **Pagination**: All list endpoints are paginated.
* **Permissions**: Ensures that users can only modify or delete their own content.
* **Data Seeding**: A management command to populate the database with sample data for testing and development.
* **API Documentation**: Integrated with drf-spectacular for OpenAPI/Swagger documentation. **It is highly recommended to use the Swagger UI for easy exploration and testing of the API endpoints, as it provides an interactive interface to send requests and inspect responses.**

---

## Models

The application uses the following models:

* **`Post`**: Represents a user's post.
    * `author` (ForeignKey to `User`): The user who created the post.
    * `created_datetime` (DateTimeField): Timestamp of post creation.
    * `title` (CharField): The title of the post.
    * `content` (TextField): The body content of the post.
    * `share_count` (PositiveIntegerField): Number of times the post has been shared.
    * `like_count` (PositiveIntegerField): Number of likes the post has received.
    * `comment_count` (PositiveIntegerField): Number of comments on the post.

* **`Share`**: Records when a user shares an `original_post`.
    * `user` (ForeignKey to `User`): The user who shared the post.
    * `original_post` (ForeignKey to `Post`): The post that was shared.
    * `created_datetime` (DateTimeField): Timestamp of the share.

* **`Like`**: Records when a user likes a `post`.
    * `user` (ForeignKey to `User`): The user who liked the post.
    * `post` (ForeignKey to `Post`): The post that was liked.
    * `created_datetime` (DateTimeField): Timestamp of the like.

* **`Comment`**: Represents a comment on a post.
    * `post` (ForeignKey to `Post`): The post the comment belongs to.
    * `author` (ForeignKey to `User`): The user who created the comment.
    * `content` (TextField): The content of the comment.
    * `created_datetime` (DateTimeField): Timestamp of comment creation.

---

## Routes (API Endpoints)

The API provides the following main routes:

### Authentication

Through swagger and/or postman you can achieve it more easily
To authenticate with the API, follow these steps:

1.  **Register a New User**:
    * Navigate to the registration endpoint: `http://127.0.0.1:8000/api/register/`
    * Send a `POST` request with a `username` and `password` in the request body (e.g., `{"username": "your_username", "password": "your_password"}`).

2.  **Obtain JWT Tokens**:
    * After successful registration (or if you already have an account), go to the token endpoint: `http://127.0.0.1:8000/api/token/`
    * Send a `POST` request with your registered `username` and `password` (e.g., `{"username": "your_username", "password": "your_password"}`).
    * The API will respond with `refresh` and `access` tokens, similar to this:
        ```json
        {
          "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
          "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
        }
        ```
    * The **`access`** token is crucial for authenticating your subsequent API requests.

3.  **Use the Access Token for Authentication**:
    * For any route requiring authentication, you must include the `access` token in the `Authorization` header of your HTTP request.
    * The header should be formatted as: `Authorization: Bearer <your_access_token>`.
    * For example, when making a `POST` request to create a new post, your headers would include `Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...`.

* `POST /apiregister/`: Register a new user.
    * Request Body: `{"username": "your_username", "password": "your_password"}`
* `POST /api/token/`: Obtain JWT access and refresh tokens.
    * Request Body: `{"username": "your_username", "password": "your_password"}`
* `POST /api/token/refresh/`: Refresh an expired access token using a refresh token.
    * Request Body: `{"refresh": "your_refresh_token"}`

### Posts

* `GET /posts/`: List all posts.
* `POST /posts/`: Create a new post (Authentication Required).
    * Request Body: `{"title": "Your Post Title", "content": "Your post content"}`
* `GET /posts/{id}/`: Retrieve a specific post by ID.
* `PATCH /posts/{id}/`: Partially update a post by ID (Author Only).
* `PUT /posts/{id}/`: Fully update a post by ID (Author Only).
* `DELETE /posts/{id}/`: Delete a post by ID (Author Only).
* `GET /posts/trending/`: List posts ordered by like count (trending posts).

### Post Interactions

* `POST /posts/{id}/like/`: Like a post (Authentication Required).
* `DELETE /posts/{id}/like/`: Unlike a post (Authentication Required).
* `POST /posts/{id}/repost/`: Share/repost a post (Authentication Required).
* `DELETE /posts/{id}/repost/`: Unshare/unrepost a post (Authentication Required).

### Comments

* `GET posts/{post_id}/comments/`: List comments for a specific post.
* `POST /posts/{post_id}/comments/`: Create a new comment on a post (Authentication Required).
    * Request Body: `{"content": "Your comment content"}`
* `GET /posts/{post_id}/comments/{id}/`: Retrieve a specific comment by ID.
* `PATCH /posts/{post_id}/comments/{id}/`: Partially update a comment by ID (Author Only).
* `PUT /posts/{post_id}/comments/{id}/`: Fully update a comment by ID (Author Only).
* `DELETE /posts/{post_id}/comments/{id}/`: Delete a comment by ID (Author Only).

### Users

* `GET /users/`: List all users.
* `GET /users/{username}/`: Retrieve a specific user by username.
* `GET /users/{username}/posts/`: List all posts by a specific user.
* `GET /users/{username}/shares/`: List all posts shared by a specific user.

---

## How to Run the Application

### Prerequisites

* Python 3.8+
* pip (Python package installer)

### Setup

1.  **Clone the repository:**

    ```bash
    git clone [https://github.com/gabriel-henrique00/CodeLeapSelectionProcess-Backend.git](https://github.com/gabriel-henrique00/CodeLeapSelectionProcess-Backend.git)
    cd CodeLeapSelectionProcess-Backend
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

    (Your `requirements.txt` should contain at least: `Django`, `djangorestframework`, `djangorestframework-simplejwt`, `drf-spectacular`, `django-cors-headers`, `django-filter`, `Faker`, `djangorestframework-nested-routers`)

4.  **Prepare and seed the database:**

    ```bash
    python manage.py makemigrations api
    python manage.py migrate
    python manage.py seed_data
    ```
6.  **Create a Django Superuser (Optional):**

If you need administrative access to the Django admin panel, you can create a superuser:

   ```bash
   python manage.py createsuperuser
   ```

5.  **Run the development server:**

    ```bash
    python manage.py runserver
    ```

    The API will be available at `http://127.0.0.1:8000/`.
    I recommend using swagger `http://127.0.0.1:8000/api/schema/swagger-ui/`

### API Documentation

Once the server is running, you can access the API documentation at:

* **Swagger UI**: `http://127.0.0.1:8000/api/schema/swagger-ui/` (Most Recommend)
* **ReDoc**: `http://127.0.0.1:8000/api/schema/redoc/`
* **OpenAPI Schema (YAML/JSON)**: `http://127.0.0.1:8000/api/schema/`

---

## Running Tests

To run the full test suite for the API, use the following command:

```bash
python manage.py test api --tag=full_suite
