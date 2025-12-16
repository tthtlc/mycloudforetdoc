package main

import (
    "context"
    "log"

    pb "github.com/tthtlc/cloudforet-demo-plugin/protos"
)

type PluginService struct {
    pb.UnimplementedCollectorPluginServer
}

// 1. Plugin Handshake
func (s *PluginService) Init(ctx context.Context, req *pb.PluginInitRequest) (*pb.PluginInitResponse, error) {
    log.Println("[Init] plugin_init called")
    return &pb.PluginInitResponse{
        Metadata: map[string]string{
            "plugin_name": "go-cloudforet-demo",
        },
    }, nil
}

// 2. Verify Credentials
func (s *PluginService) Verify(ctx context.Context, req *pb.PluginVerifyRequest) (*pb.PluginVerifyResponse, error) {
    log.Printf("[Verify] got secret data: %v\n", req.SecretData)
    return &pb.PluginVerifyResponse{}, nil
}

// 3. Get Plugin Metadata (spacectl enumerates this)
func (s *PluginService) GetPluginInfo(ctx context.Context, req *pb.PluginInfoRequest) (*pb.PluginInfoResponse, error) {
    return &pb.PluginInfoResponse{
        PluginId:   "go-cloudforet-demo",
        Version:    "1.0.0",
        Options:    map[string]string{"language": "go"},
    }, nil
}

// 4. List Supported Methods (IMPORTANT FOR spacectl!!)
func (s *PluginService) GetTasks(ctx context.Context, req *pb.PluginTasksRequest) (*pb.PluginTasksResponse, error) {
    return &pb.PluginTasksResponse{
        Tasks: []string{
            "collect_resources",
            "health_check",
        },
    }, nil
}

// 5. Actual Task Handler (optional)
func (s *PluginService) Collect(ctx context.Context, req *pb.CollectRequest) (*pb.CollectResponse, error) {
    log.Println("[Collect] running dummy collector")

    return &pb.CollectResponse{
        Results: []*pb.CollectResult{
            {
                State:  "SUCCESS",
                Message: "Dummy collection completed",
                Resource: map[string]string{"example": "value"},
            },
        },
    }, nil
}

