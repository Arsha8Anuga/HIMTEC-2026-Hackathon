FROM golang:1.24-alpine AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o /server ./cmd/server

FROM alpine:3.20
# Server membaca migrations/ dan data/ secara relatif terhadap direktori kerja.
WORKDIR /app
COPY --from=build /server /app/server
COPY migrations migrations
COPY data data
EXPOSE 8080
CMD ["/app/server"]
