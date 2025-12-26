DROP DATABASE RecruitmentApp;
CREATE DATABASE RecruitmentApp;
\c RecruitmentApp;


CREATE TYPE role_enum AS ENUM ('student','company','admin');
CREATE TYPE application_status_enum AS ENUM ('applied','testing','interviewing','offered','rejected');
CREATE TYPE offer_status_enum AS ENUM ('pending','accepted','rejected');

DROP TABLE IF EXISTS interview_feedbacks CASCADE;
DROP TABLE IF EXISTS interviews CASCADE;
DROP TABLE IF EXISTS evaluation CASCADE;
DROP TABLE IF EXISTS offers CASCADE;
DROP TABLE IF EXISTS test_results CASCADE;
DROP TABLE IF EXISTS skill_tests CASCADE;
DROP TABLE IF EXISTS job_skills CASCADE;
DROP TABLE IF EXISTS student_skills CASCADE;
DROP TABLE IF EXISTS application CASCADE;
DROP TABLE IF EXISTS jobs CASCADE;
DROP TABLE IF EXISTS skills CASCADE;
DROP TABLE IF EXISTS student_profiles CASCADE;
DROP TABLE IF EXISTS reports CASCADE;
DROP TABLE IF EXISTS companies CASCADE;
DROP TABLE IF EXISTS student CASCADE;
DROP TABLE IF EXISTS notification CASCADE;
DROP TABLE IF EXISTS users CASCADE;

CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password VARCHAR(255) NOT NULL,
  role role_enum NOT NULL,
  status VARCHAR(50),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE student (
  id SERIAL PRIMARY KEY,
  full_name VARCHAR(255),
  dob DATE,
  major VARCHAR(255),
  user_id INT UNIQUE NOT NULL,
  cccd VARCHAR(50),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE company (
  id SERIAL PRIMARY KEY,
  company_name VARCHAR(255),
  description TEXT,
  website VARCHAR(255),
  user_id INT UNIQUE NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE student_profile (
  id SERIAL PRIMARY KEY,
  student_id INT UNIQUE NOT NULL,
  cv_url TEXT,
  portfolio_url TEXT,
  "educationLevel" VARCHAR(100),
  degrees TEXT,
  about TEXT,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE
);

CREATE TABLE skill (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255),
  category VARCHAR(255)
);

CREATE TABLE student_skill (
  student_id INT NOT NULL,
  skill_id INT NOT NULL,
  level INT,
  PRIMARY KEY (student_id, skill_id),
  FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE,
  FOREIGN KEY (skill_id) REFERENCES skill(id) ON DELETE CASCADE
);

CREATE TABLE job (
  id SERIAL PRIMARY KEY,
  title VARCHAR(255),
  description TEXT,
  location VARCHAR(255),
  status VARCHAR(50),
  company_id INT NOT NULL,
  FOREIGN KEY (company_id) REFERENCES company(id) ON DELETE CASCADE
);

CREATE TABLE job_skill (
  job_id INT NOT NULL,
  skill_id INT NOT NULL,
  required_level INT,
  PRIMARY KEY (job_id, skill_id),
  FOREIGN KEY (job_id) REFERENCES job(id) ON DELETE CASCADE,
  FOREIGN KEY (skill_id) REFERENCES skill(id) ON DELETE CASCADE
);

CREATE TABLE application (
  id SERIAL PRIMARY KEY,
  student_id INT NOT NULL,
  job_id INT NOT NULL,
  status application_status_enum NOT NULL,
  applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE,
  FOREIGN KEY (job_id) REFERENCES job(id) ON DELETE CASCADE
);

CREATE TABLE skill_test (
  id SERIAL PRIMARY KEY,
  test_name VARCHAR(255),
  duration INT,
  total_score INT,
  job_id INT NOT NULL,
  FOREIGN KEY (job_id) REFERENCES job(id) ON DELETE CASCADE
);

CREATE TABLE test_result (
  id SERIAL PRIMARY KEY,
  test_id INT NOT NULL,
  student_id INT NOT NULL,
  score INT,
  submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (test_id) REFERENCES skill_test(id) ON DELETE CASCADE,
  FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE
);

CREATE TABLE interview (
  id SERIAL PRIMARY KEY,
  application_id INT NOT NULL,
  interview_date TIMESTAMP,
  interview_type VARCHAR(100),
  status VARCHAR(50),
  FOREIGN KEY (application_id) REFERENCES application(id) ON DELETE CASCADE
);

CREATE TABLE interview_feedback (
  id SERIAL PRIMARY KEY,
  interview_id INT UNIQUE NOT NULL,
  feedback TEXT,
  rating INT,
  FOREIGN KEY (interview_id) REFERENCES interview(id) ON DELETE CASCADE
);

CREATE TABLE evaluation (
  id SERIAL PRIMARY KEY,
  application_id INT UNIQUE NOT NULL,
  skill_score INT,
  peer_review TEXT,
  improvement TEXT,
  FOREIGN KEY (application_id) REFERENCES application(id) ON DELETE CASCADE
);

CREATE TABLE offer (
  id SERIAL PRIMARY KEY,
  application_id INT UNIQUE NOT NULL,
  offer_detail TEXT,
  status offer_status_enum NOT NULL,
  FOREIGN KEY (application_id) REFERENCES application(id) ON DELETE CASCADE
);

CREATE TABLE notification (
  id SERIAL PRIMARY KEY,
  user_id INT NOT NULL,
  content TEXT,
  is_read BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE report (
  id SERIAL PRIMARY KEY,
  report_type VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  company_id INT NOT NULL,
  FOREIGN KEY (company_id) REFERENCES company(id) ON DELETE CASCADE
);
