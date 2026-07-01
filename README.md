# Banking API with FastAPI

A comprehensive banking API built with FastAPI, featuring transaction management, report generation, and JWT authentication.

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![JWT](https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=JSON%20web%20tokens&logoColor=white)](https://jwt.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Database Migrations](#-database-migrations)
- [Running the Application](#-running-the-application)
- [API Documentation](#-api-documentation)
- [API Endpoints](#-api-endpoints)
- [Authentication](#-authentication)
- [Reports](#-reports)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

### 🔐 Authentication & Authorization
- JWT-based authentication
- Role-based access control (Admin/Customer)
- Password hashing with bcrypt
- Token expiration and refresh

### 👤 User Management
- User registration (must have customer profile)
- User login with JWT token
- User profile management
- Role management (Admin/Customer)

### 💳 Account Management
- Create accounts (Savings/Current)
- View account details
- Update account information
- Close accounts
- Account status management (Active/Dormant/Frozen/Blocked/Closed)
- Account balance inquiry

### 💰 Transaction Operations
- **Deposits**: Add money to accounts
- **Withdrawals**: Remove money from accounts
- **Transfers**: Transfer money between accounts
- Transaction reference numbers
- Atomic transactions (all-or-nothing)
- Balance validation (no overdraft)
- Account status validation

### 📊 Transaction History
- Advanced filtering (by type, status, date, amount)
- Pagination and sorting
- Search by reference or remarks
- Customer-specific transaction history
- Transaction summary and statistics

### 📈 Reports
- **Customer Reports**: CSV, Excel, PDF export
- **Account Reports**: CSV, Excel, PDF export
- **Transaction Reports**: CSV, Excel, PDF export
- **Summary Reports**: Combined statistics
- Date range filtering

### 🔒 Security
- JWT token-based authentication
- Password hashing with bcrypt
- SQL injection prevention (SQLAlchemy ORM)
- Input validation (Pydantic)
- CORS configuration
- Environment variables for sensitive data

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI 0.104.1
- **ORM**: SQLAlchemy 2.0.23
- **Database**: PostgreSQL
- **Migrations**: Alembic 1.12.1
- **Authentication**: JWT (python-jose)
- **Password Hashing**: bcrypt (passlib)
- **Validation**: Pydantic 2.5.0
- **Configuration**: Pydantic Settings

### Reports
- **CSV**: Python CSV module
- **Excel**: OpenPyXL 3.1.2
- **PDF**: ReportLab 4.0.9

### Development
- **Server**: Uvicorn
- **Environment**: Python 3.11+
- **Package Manager**: pip
- **Version Control**: Git


## 🚀 Installation

### Prerequisites
- Python 3.11 or higher
- PostgreSQL 14 or higher
- pip (Python package manager)


### Step 1: Clone the Repositorybash 
```bash
cd BankingAPI-with-FastAPI
git clone https://github.com/Leepak/BankingAPI-with-FastAPI.git
```
### Step 2: Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```
### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```
### Step 4: Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env
```
### Step 5: Set Up Database
```bash
# Create PostgreSQL database
sudo -u postgres psql
CREATE DATABASE banking_db;
CREATE USER banking_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE banking_db TO banking_user;
\q
```
### Step 6: Run Migrations
```bash
# Run database migrations
alembic upgrade head
```
⚙️ Configuration
Environment Variables
```bash
Create a .env file with the following variables:

env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/banking_db

# JWT Configuration
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Server Configuration
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=INFO

# Security
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
Generate SECRET_KEY
```
Generate SECRET_KEY
```bash
# Generate a secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
Database Migrations
Create a Migration
```bash
alembic revision --autogenerate -m "description_of_changes"
```
Apply Migrations
```bash
# Apply all migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Check current version
alembic current
```
Running the Application
Development Mode
```bash
# Run with auto-reload
uvicorn app.main:app --reload
```
Production Mode
```bash
# Run without auto-reload
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Or use gunicorn (for production)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```
Using Docker
```bash
# Build and run with Docker Compose
docker-compose up --build

# Stop containers
docker-compose down
```
