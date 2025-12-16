
package main

import (
    "log"
    "net"

    "google.golang.org/grpc"
    pb "github.com/tthtlc/cloudforet-demo-plugin/protos"
)

func StartGRPCServer() {
    lis, err := net.Listen("tcp", ":50051")
    if err != nil {
        log.Fatalf("failed to listen: %v", err)
    }

    grpcServer := grpc.NewServer()

    // Register plugin service
    pb.RegisterCollectorPluginServer(grpcServer, &PluginService{})

    log.Println("Cloudforet Plugin gRPC server running on :50051")
    if err := grpcServer.Serve(lis); err != nil {
        log.Fatalf("failed to serve: %v", err)
    }
}

