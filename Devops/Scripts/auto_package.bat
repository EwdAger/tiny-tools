@echo off
chcp 65001
CLS
SET /p name=请输入镜像名和版本号(如：mfa:1.0):

echo 镜像名为 %name%

echo 正在登陆harbor镜像仓库
docker login registry.getech.cn

echo 正在本地构建镜像
docker build -t %name% .


echo 正在给本地镜像打远程标签
docker tag %name% registry.getech.cn/mfa/%name%

echo 正在推送到远端镜像仓库
docker push registry.getech.cn/mfa/%name%


echo 打包完毕！
pause