# 介绍

docker-compose 中常用到的等待某服务完全启动（比如mysql）的脚本

# 使用方法

```yaml
hello-world-worker:
    image: xxxxxxxx
    environment:
      TZ: Asia/Shanghai
    restart: always
    links:
      - mysql

    command: ["./wait-for-it.sh", "mysql:3306", '-t', '0', "--", "celery", "-A", "add_tasks.celery_app", "worker", "-c", "2", "-l", "info"]

```