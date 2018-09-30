import grpc_tools.protoc
import os


def replace_file(pb2_grpc, protos_name):
    backupfilename = pb2_grpc + ".bak"
    to_replace = "import " + protos_name
    replace_with = "import grpcdemo.common.internal." + protos_name
    os.replace(pb2_grpc, backupfilename)
    with open(backupfilename, mode='rb') as backupfile:
        data = backupfile.read(500 * 1024)
        if len(data) == 500 * 1024:
            raise Exception(pb2_grpc + "is too big")
    with open(pb2_grpc, mode='wb') as grpc_file:
        grpc_file.write(data.replace(to_replace.encode(), replace_with.encode()))
    os.unlink(backupfilename)


if __name__ == "__main__":
    # python -m grpc_tools.protoc -I./proto --python_out=./internal --grpc_python_out=./internal ./proto/instance.proto
    os.chdir('./proto')
    for proto in os.listdir():
        if proto.endswith('.proto'):
            args = ["-I.",
                    "--python_out=../internal",
                    "--grpc_python_out=../internal",
                    proto
                    ]
            grpc_tools.protoc.main(args)

            protos_name = proto[:-6]
            pb2_grpc = "../internal/" + protos_name + "_pb2_grpc.py"
            replace_file(pb2_grpc, protos_name)
            pb2= "../internal/" + protos_name + "_pb2.py"
            replace_file(pb2, 'common_pb2')