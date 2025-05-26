-- init.sql

-- 구직자 테이블 생성
CREATE TABLE IF NOT EXISTS jobseeker (
  id VARCHAR(50) PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  password VARCHAR(100) NOT NULL,
  email VARCHAR(100) NOT NULL,
  phone VARCHAR(20) NOT NULL,
  resume LONGBLOB
);

-- 고용자 테이블 생성
CREATE TABLE IF NOT EXISTS employer (
  id VARCHAR(50) PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  password VARCHAR(100) NOT NULL,
  email VARCHAR(100) NOT NULL,
  phone VARCHAR(20) NOT NULL,
  image_url VARCHAR(255)
);
