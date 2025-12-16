
## enumeara

docker build -t tthtlc/cloudforet-demo-plugin:latest .

docker push tthtlc/cloudforet-demo-plugin:latest

spacectl exec get plugin.PluginInfo -f info.yaml

spacectl exec register repository.Plugin -f plugin.yaml

grpcurl -plaintext localhost:50051 list

