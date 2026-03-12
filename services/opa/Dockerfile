FROM openpolicyagent/opa:latest
COPY policies /policies
CMD ["run", "--server", "--addr=0.0.0.0:8181", "/policies"]
