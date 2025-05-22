# 📦 사용 방법 (macOS 기준)


## 1️⃣ 필수 패키지 설치

```bash
pip install SQLAlchemy
```

```bash
pip install Flask-SQLAlchemy
```

```bash
pip install pymysql
```

## 2️⃣ MySQL 실행 및 DB 생성

```bash
mysql -u root -p
```

```sql
CREATE DATABASE packet_logs_db;
```

```sql
SHOW DATABASES;
```

packet_logs_db가 출력되면 성공

- sql프롬프트 나가는법

```bash
exit;
```

### 데이터베이스 확인방법

```bash
mysql -u root
```

```sql
USE packet_logs_db;
```

```sql
SHOW TABLES;
```

```sql
SELECT * FROM packet_log;
```