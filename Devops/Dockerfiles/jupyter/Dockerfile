FROM jupyter/datascience-notebook:python-3.7.6

MAINTAINER ewdager "ningwenjie@getech.cn"

WORKDIR /home/jovyan

ENV NB_USER=ewdager

ENV CHOWN_HOME=yes

ENV CHOWN_EXTRA_OPTS=-R

USER root

WORKDIR /home/ewdager

COPY --chown=${NB_UID}:${NB_GID} requirements.txt /tmp/

RUN pip install -r /tmp/requirements.txt -i https://pypi.douban.com/simple

CMD ["jupyter", "notebook", "--port=8888", "--no-browser", "--ip=0.0.0.0", "--allow-root", "--NotebookApp.token='123456'"]