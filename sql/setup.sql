-- Active: 1765626014516@@127.0.0.1@3306@mysql
# root 계정으로 실행

# lcdb 생성
create database lcdb character set utf8mb4 collate utf8mb4_unicode_ci;

# django 사용자에게 lcdb 권한 부여
grant all privileges on lcdb.* to 'django'@'%';



-- create user django@'%' IDENTIFIED by 'django';
