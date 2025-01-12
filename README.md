# Distributed Server System

A system based on 5 dockerized applications communicating via a Docker bridge network. The Coordinator manages 3 separate servers, which handle fragments of data and send them to the Client. The Client then validates and processes the received data.

## Components:
1. **Coordinator**: Manages the servers and facilitates communication.
2. **Servers (3)**: Serve fragments of data based on client requests.
3. **Client**: Receives, validates, and processes the data.
