
FROM golang:1.22 AS builder

WORKDIR /app
COPY . .

RUN go mod tidy
RUN go build -o plugin-server main.go server.go service.go

FROM gcr.io/distroless/base
COPY --from=builder /app/plugin-server /plugin-server

ENTRYPOINT ["/plugin-server"]

