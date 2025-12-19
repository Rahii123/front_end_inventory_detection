# AI Vision Pro - Frontend

This is the frontend application for the Image Detection Model, built with FastAPI and Jinja2 templates.

## specific Features
- **Premium UI**: Glassmorphism design, responsive dashboard, and modern aesthetics.
- **Authentication**: Login system with secure password hashing.
- **Dashboard**: Real-time status of models and jobs.
- **Training**: Interface to configure and start model training (Epochs, Batch Size, etc.).
- **Prediction**: Image upload and classification interface.
- **Database**: MySQL integration for storing users and training jobs.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Variables**:
    Ensure `.env` file exists with your MySQL configuration:
    ```env
    PORT=8000
    MYSQL_HOST=localhost
    MYSQL_USER=root
    MYSQL_PASSWORD=your_password
    MYSQL_DATABASE=my_database
    MYSQL_PORT=3306
    ```

3.  **Run the Application**:
    ```bash
    uvicorn app.main:app --reload --port 8000
    ```

4.  **Access the App**:
    Open [http://localhost:8000](http://localhost:8000) in your browser.
    - **Default User**: `admin`
    - **Default Password**: `admin123`
