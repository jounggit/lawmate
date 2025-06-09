-- DB 마이그레이션 스크립트: 법령 및 판례 테이블 추가

-- 1. Law 테이블 수정
CREATE TABLE IF NOT EXISTS Law_new (
    law_id INT AUTO_INCREMENT PRIMARY KEY,
    law_code VARCHAR(20) UNIQUE NOT NULL,
    law_name VARCHAR(100) NOT NULL,
    law_type VARCHAR(50),
    promulgation_date VARCHAR(10),
    link TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 기존 Law 테이블이 있으면 데이터 이전
INSERT INTO Law_new (law_id, law_code, law_name)
SELECT law_id, CONCAT('legacy-', law_id), law_name
FROM Law
WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'Law');

-- 기존 테이블 삭제 및 새 테이블로 교체
DROP TABLE IF EXISTS Law;
ALTER TABLE Law_new RENAME TO Law;

-- 2. Law_Article 테이블 생성
CREATE TABLE IF NOT EXISTS Law_Article (
    article_id INT AUTO_INCREMENT PRIMARY KEY,
    law_id INT NOT NULL,
    article_number VARCHAR(50) NOT NULL,
    article_title VARCHAR(200),
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (law_id) REFERENCES Law(law_id),
    UNIQUE KEY uix_law_article (law_id, article_number)
);

-- 3. Precedent 테이블 수정
CREATE TABLE IF NOT EXISTS Precedent_new (
    precedent_id INT AUTO_INCREMENT PRIMARY KEY,
    case_number VARCHAR(100) UNIQUE NOT NULL,
    case_name VARCHAR(200),
    court VARCHAR(100),
    decision_date VARCHAR(10),
    summary TEXT,
    judgment_text TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 기존 Precedent 테이블이 있으면 데이터 이전
INSERT INTO Precedent_new (precedent_id, case_number, case_name, decision_date, summary, judgment_text)
SELECT precedent_id, aCase_number, aCase, decision_date, summary, judgment_text
FROM Precedent
WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'Precedent');

-- 기존 테이블 삭제 및 새 테이블로 교체
DROP TABLE IF EXISTS Precedent;
ALTER TABLE Precedent_new RENAME TO Precedent;

-- 4. aCase_Law 테이블 생성 (aCase와 법령/조문 연결)
CREATE TABLE IF NOT EXISTS aCase_Law (
    id INT AUTO_INCREMENT PRIMARY KEY,
    aCase_id INT NOT NULL,
    law_id INT NOT NULL,
    article_id INT,
    relevance_score INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (aCase_id) REFERENCES aCase(aCase_id),
    FOREIGN KEY (law_id) REFERENCES Law(law_id),
    FOREIGN KEY (article_id) REFERENCES Law_Article(article_id),
    UNIQUE KEY uix_case_law_article (aCase_id, law_id, article_id)
);

-- 5. aCase_Precedent 테이블 생성 (aCase와 판례 연결)
CREATE TABLE IF NOT EXISTS aCase_Precedent (
    id INT AUTO_INCREMENT PRIMARY KEY,
    aCase_id INT NOT NULL,
    precedent_id INT NOT NULL,
    relevance_score INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (aCase_id) REFERENCES aCase(aCase_id),
    FOREIGN KEY (precedent_id) REFERENCES Precedent(precedent_id),
    UNIQUE KEY uix_case_precedent (aCase_id, precedent_id)
);
