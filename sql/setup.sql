# root 계정으로 실행

# lcdb 생성
create database lcdb character set utf8mb4 collate utf8mb4_unicode_ci;

# django 사용자에게 lcdb 권한 부여
grant all privileges on lcdb.* to 'django'@'%';