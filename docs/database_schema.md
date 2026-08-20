# Database Schema — AUSA

## Overview

The database stores:
- Student profiles
- University programs
- Scholarships
- (Optional) Historical admitted student profiles for benchmarking

## Tables

### 1. students
Stores the academic profile entered by the user.

| Column                | Type           | Description                          |
|-----------------------|----------------|--------------------------------------|
| id                    | SERIAL PK      | Unique ID                            |
| gpa                   | DECIMAL(3,2)   | Grade Point Average                  |
| ielts                 | DECIMAL(3,1)   | IELTS score                          |
| toefl                 | INTEGER        | TOEFL score (optional)               |
| degree_level          | VARCHAR(20)    | bachelor / master / phd              |
| field_of_study        | VARCHAR(100)   | Desired field                        |
| country               | VARCHAR(50)    | Preferred country                    |
| research_experience   | BOOLEAN        | Has research experience              |
| projects              | TEXT           | Description of projects              |
| budget                | VARCHAR(50)    | Budget level                         |
| goals                 | TEXT           | Student goals                        |
| created_at            | TIMESTAMP      | Creation time                        |

### 2. programs
University programs with official requirements.

| Column             | Type           | Description                          |
|--------------------|----------------|--------------------------------------|
| id                 | SERIAL PK      | Unique ID                            |
| university_name    | VARCHAR(200)   | University name                      |
| program_name       | VARCHAR(300)   | Program name                         |
| degree_level       | VARCHAR(20)    | bachelor / master / phd              |
| field              | VARCHAR(100)   | Field of study                       |
| country            | VARCHAR(50)    | Country                              |
| min_gpa            | DECIMAL(3,2)   | Minimum GPA requirement              |
| min_ielts          | DECIMAL(3,1)   | Minimum IELTS                        |
| min_toefl          | INTEGER        | Minimum TOEFL                        |
| tuition_fee        | DECIMAL(10,2)  | Tuition fee                          |
| currency           | VARCHAR(10)    | Currency (EUR, USD, GBP...)          |
| deadline           | DATE           | Application deadline                 |
| requirements_text  | TEXT           | Full requirements text               |
| source_url         | TEXT           | Official source link                 |
| last_updated       | DATE           | Last update date                     |
| is_active          | BOOLEAN        | Is program currently active          |

### 3. scholarships
Scholarship and grant opportunities.

| Column             | Type           | Description                          |
|--------------------|----------------|--------------------------------------|
| id                 | SERIAL PK      | Unique ID                            |
| name               | VARCHAR(300)   | Scholarship name                     |
| provider           | VARCHAR(200)   | Organization                         |
| country            | VARCHAR(50)    | Country                              |
| degree_level       | VARCHAR(20)    | Target degree level                  |
| min_gpa            | DECIMAL(3,2)   | Minimum GPA                          |
| min_ielts          | DECIMAL(3,1)   | Minimum IELTS                        |
| eligibility_text   | TEXT           | Eligibility conditions               |
| amount             | TEXT           | Funding amount                       |
| deadline           | DATE           | Deadline                             |
| source_url         | TEXT           | Official source                      |
| last_updated       | DATE           | Last update                          |

### 4. admitted_profiles (optional)
Historical profiles of previously admitted students (for benchmarking only).

| Column             | Type           | Description                          |
|--------------------|----------------|--------------------------------------|
| id                 | SERIAL PK      | Unique ID                            |
| program_id         | INTEGER FK     | Related program                      |
| gpa                | DECIMAL(3,2)   | Admitted student GPA                 |
| ielts              | DECIMAL(3,1)   | IELTS score                          |
| research_experience| BOOLEAN        | Had research experience              |
| source             | VARCHAR(100)   | Data source (GradCafe, etc.)         |
| notes              | TEXT           | Additional notes                     |