# Demo of use gRPC in python service

### 项目结构
```
.
├── grpcdemo
│   ├── __pycache__
│   ├── api  包含server端对RPC方法的具体实现
│   │   ├
│   │   └── grpc
│   ├── common 包含proto定义的消息和RPC方法，及编译后的python代码
│   │   ├
│   │   ├── internal  编译后代码
│   │   └── proto  proto 定义
│   └── server gRPC服务启动相关模块
│       └──
└── tests  测试用例模块
    ├── __pycache__
    └── unit
        ├── __pycache__
        └── api

```

### 环境要求
python 3.6+

### 示例过程：
1. 安装依赖：
```
cd grpcdemo
virtualenv -p python3 venv
source venv/bin/activate
python setup.py install
```
2. 启动gRPC服务：

```
cd grpcdemo
python main.py
```

3. 启动测试用例:

```
python -m unittest tests/unit/api/test_grpc.py
```

### gRPC模式
项目内包含三种gRPC模式的示例，分别是：
1. 简单RPC，即请求-响应均非流式；
2. 流式响应RPC；
3. 双向流式RPC；
以上三种是在之前实际项目中应用比较多的方式，还有一种流式请求-非流式响应的模式，暂时没有具体应用场景。


### 使用gRPC的过程介绍
1. 定义protocol buffers消息格式及RPC方法；
2. 将protocol buffers编译为具体语言代码；
3. 在server端具体实现RPC方法，按照消息格式和RPC类型(流式/非流式)处理响应;
4. client端调用client stub方法，获取响应；