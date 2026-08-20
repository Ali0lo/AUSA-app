-- AUSA Database Schema
-- PostgreSQL

-- ======================
-- 1. Students
-- ======================
CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    gpa DECIMAL(3,2),
    ielts DECIMAL(3,1),
    toefl INTEGER,
    degree_level VARCHAR(20) CHECK (degree_level IN ('bachelor', 'master', 'phd')),
    field_of_study VARCHAR(100),
    country VARCHAR(50),
    research_experience BOOLEAN DEFAULT FALSE,
    projects TEXT,
    budget VARCHAR(50),
    goals TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ======================
-- 2. Programs
-- ======================
CREATE TABLE IF NOT EXISTS programs (
    id SERIAL PRIMARY KEY,
    university_name VARCHAR(200) NOT NULL,
    program_name VARCHAR(300) NOT NULL,
    degree_level VARCHAR(20) CHECK (degree_level IN ('bachelor', 'master', 'phd')),
    field VARCHAR(100),
    country VARCHAR(50),
    min_gpa DECIMAL(3,2),
    min_ielts DECIMAL(3,1),
    min_toefl INTEGER,
    tuition_fee DECIMAL(10,2),
    currency VARCHAR(10) DEFAULT 'EUR',
    deadline DATE,
    requirements_text TEXT,
    source_url TEXT,
    last_updated DATE DEFAULT CURRENT_DATE,
    is_active BOOLEAN DEFAULT TRUE
);

-- ======================
-- 3. Scholarships
-- ======================
CREATE TABLE IF NOT EXISTS scholarships (
    id SERIAL PRIMARY KEY,
    name VARCHAR(300) NOT NULL,
    provider VARCHAR(200),
    country VARCHAR(50),
    degree_level VARCHAR(20),
    min_gpa DECIMAL(3,2),
    min_ielts DECIMAL(3,1),
    eligibility_text TEXT,
    amount TEXT,
    deadline DATE,
    source_url TEXT,
    last_updated DATE DEFAULT CURRENT_DATE
);

-- ======================
-- 4. Admitted Profiles (optional, for benchmarking)
-- ======================
CREATE TABLE IF NOT EXISTS admitted_profiles (
    id SERIAL PRIMARY KEY,
    program_id INTEGER REFERENCES programs(id) ON DELETE SET NULL,
    gpa DECIMAL(3,2),
    ielts DECIMAL(3,1),
    research_experience BOOLEAN,
    source VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ======================
-- Indexes for faster search
-- ======================
CREATE INDEX IF NOT EXISTS idx_programs_country ON programs(country);
CREATE INDEX IF NOT EXISTS idx_programs_degree ON programs(degree_level);
CREATE INDEX IF NOT EXISTS idx_programs_field ON programs(field);
CREATE INDEX IF NOT EXISTS idx_scholarships_country ON scholarships(country);