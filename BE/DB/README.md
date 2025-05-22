# 📦 사용 방법 (macOS 기준)


## 1️⃣ (실행 전) 필수 패키지 설치

#### SQLAlchemy 설치
```bash
pip install SQLAlchemy
```

#### Flask-SQLAlchemy 설치
```bash
pip install Flask-SQLAlchemy
```

#### pymysql 설치
```bash
pip install pymysql
```

## 2️⃣ (실행 전) MySQL 실행 및 DB 생성

#### root계정으로 MySQL 로그인
```bash
mysql -u root -p
```

#### (sql) 'packet_logs_db' 생성
```sql
CREATE DATABASE packet_logs_db;
```

#### (sql) 데이터베이스에 'packet_logs_db' 생성되었는지 확인
```sql
SHOW DATABASES;
```

packet_logs_db가 출력되면 성공

- sql프롬프트 나가는법 (sql)

```bash
exit;
```

## 3️⃣ (실행 후) 데이터베이스 확인방법

#### root계정으로 MySQL 로그인
```bash
mysql -u root
```

#### 작업할 DB를 packet_logs_db로 설정
```sql
USE packet_logs_db;
```

#### 선택한 DB의 테이블 목록 정렬
```sql
SHOW TABLES;
```
packet_log가 존재하면 성공


#### packet_log에 존재하는 모든 정보 조회
```sql
SELECT * FROM packet_log;
```
