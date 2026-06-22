29.06   File "/usr/lib/python3/dist-packages/launchpadlib/launchpad.py", line 144, in _request
29.06     response, content = super(LaunchpadOAuthAwareHttp, self)._request(
29.06   File "/usr/lib/python3/dist-packages/lazr/restfulclient/_browser.py", line 184, in _request
29.06     return super(RestfulHttp, self)._request(
29.06   File "/usr/lib/python3/dist-packages/httplib2/__init__.py", line 1441, in _request
29.06     (response, content) = self._conn_request(conn, request_uri, method, body, headers)
29.06   File "/usr/lib/python3/dist-packages/httplib2/__init__.py", line 1363, in _conn_request
29.06     conn.connect()
29.06   File "/usr/lib/python3/dist-packages/httplib2/__init__.py", line 1199, in connect
29.06     raise socket_err
29.06   File "/usr/lib/python3/dist-packages/httplib2/__init__.py", line 1153, in connect
29.06     sock.connect((self.host, self.port))
29.06 OSError: [Errno 101] Network is unreachable
------
[+] build 0/1
 ⠙ Image reconnaissance-faciale-projet-dell-technologies-facial-recognition-app Building                                                                                                                                                31.0s
Dockerfile:15

--------------------

  14 |     # 2. Installation de Python 3.11 et des bibliothèques système (OpenCV + MediaPipe)

  15 | >>> RUN apt-get update && apt-get install -y software-properties-common && \

  16 | >>>     add-apt-repository ppa:deadsnakes/ppa -y && \

  17 | >>>     apt-get update && apt-get install -y \

  18 | >>>     python3.11 \

  19 | >>>     python3.11-dev \

  20 | >>>     python3.11-distutils \

  21 | >>>     git \

  22 | >>>     cmake \

  23 | >>>     libgl1-mesa-glx \

  24 | >>>     libglib2.0-0 \

  25 | >>>     libsm6 \

  26 | >>>     libxext6 \

  27 | >>>     libxrender-dev \

  28 | >>>     curl \

  29 | >>>     libgles2 \

  30 | >>>     libegl1 \

  31 | >>>     && rm -rf /var/lib/apt/lists/*

  32 |

--------------------

failed to solve: process "/bin/sh -c apt-get update && apt-get install -y software-properties-common &&     add-apt-repository ppa:deadsnakes/ppa -y &&     apt-get update && apt-get install -y     python3.11     python3.11-dev     python3.11-distutils     git     cmake     libgl1-mesa-glx     libglib2.0-0     libsm6     libxext6     libxrender-dev     curl     libgles2     libegl1     && rm -rf /var/lib/apt/lists/*" did not complete successfully: exit code: 1

ub_admin@b02-34-c4140:~/Reconnaissance-Faciale-Projet-Dell-Technologies$ ^C
