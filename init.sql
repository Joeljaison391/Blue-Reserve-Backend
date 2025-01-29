-- Employees Table
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    bluDollar_used DECIMAL(10, 2) DEFAULT 0,
    manager_id VARCHAR(255) NOT NULL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    FOREIGN KEY (manager_id) REFERENCES manager(id)
);

-- Managers Table
CREATE TABLE managers (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    bluDollar_balance DECIMAL(10, 2) DEFAULT 0, -- BluDollar balance for the manager's team
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seats Table
CREATE TABLE seats (
    id BIGSERIAL PRIMARY KEY,
    table_id INT NOT NULL,
    seat_number INT NOT NULL CHECK (seat_number BETWEEN 1 AND 4),
    location VARCHAR(255) NOT NULL,
    status VARCHAR(50) CHECK (status IN ('AVAILABLE', 'RESERVED', 'RELEASED')) DEFAULT 'AVAILABLE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reservations Table
CREATE TABLE reservations (
    id BIGSERIAL PRIMARY KEY,
    seat_id BIGINT NOT NULL REFERENCES seats(id) ON DELETE CASCADE,
    employee_id BIGINT NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    status VARCHAR(50) CHECK (status IN ('RESERVED', 'CANCELED', 'RELEASED')) DEFAULT 'RESERVED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transactions Table
CREATE TABLE transactions (
    id BIGSERIAL PRIMARY KEY,
    manager_id BIGINT NOT NULL REFERENCES managers(id) ON DELETE CASCADE,
    employee_id BIGINT NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    amount DECIMAL(10, 2) NOT NULL,
    type VARCHAR(50) CHECK (type IN ('ALLOCATION', 'RESERVATION', 'PENALTY', 'BOOST')) NOT NULL,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);