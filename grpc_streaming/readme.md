# grpc-streaming

```shell
API_PATH=grpc_streaming/grpc_api
python -m grpc_tools.protoc --proto_path=$API_PATH --python_out=$API_PATH --grpc_python_out=$API_PATH s2t.proto
```

* package in .proto-file: `The .proto file starts with a package declaration, which helps to prevent naming conflicts between different projects. In Python, packages are normally determined by directory structure, so the package you define in your .proto file will have no effect on the generated code. However, you should still declare one to avoid name collisions in the Protocol Buffers name space as well as in non-Python languages.`
