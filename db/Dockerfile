FROM postgres:14

# Set up environment variables
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=password
ENV POSTGRES_DB=blu_reserve

# Copy the initialization script
COPY ../init.sql /docker-entrypoint-initdb.d/
