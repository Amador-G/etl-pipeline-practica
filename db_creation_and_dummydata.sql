-- ORIGEN: los datos crudos, tal como "llegan" del sistema fuente
CREATE DATABASE IF NOT EXISTS etl_origen;
USE etl_origen;

CREATE TABLE fondos (
    id_fondo INT PRIMARY KEY,
    nombre VARCHAR(100),
    tipo VARCHAR(50)
);

INSERT INTO fondos (id_fondo, nombre, tipo) VALUES
(1, 'Global Equity Fund', 'Equity'),
(2, 'Fixed Income Fund',  'Bonds'),
(3, 'Real Estate Fund',   'Real Estate');

CREATE TABLE inversores (
    id_inversor INT PRIMARY KEY,
    nombre VARCHAR(100),
    id_fondo INT,
    email VARCHAR(100)
);

INSERT INTO inversores (id_inversor, nombre, id_fondo, email) VALUES
(101, 'Inversor A', 1, 'a@ejemplo.com'),
(102, 'Inversor B', 1, 'b@ejemplo.com'),
(104, 'Inversor D', 2, ''),
(106, 'Inversor F', 3, 'f@ejemplo.com'),
(108, 'Inversor H', 2, 'h@ejemplo.com'),
(110, 'Inversor J', 99, 'j@ejemplo.com');

CREATE TABLE transacciones (
    id INT PRIMARY KEY,
    fecha DATE,
    id_inversor INT,
    monto DECIMAL(15,2),
    moneda VARCHAR(3)
);

INSERT INTO transacciones (id, fecha, id_inversor, monto, moneda) VALUES
(1, '2026-01-15', 101, 5000.00, 'USD'),
(2, '2026-01-16', 102, 3200.50, 'USD'),
(3, '2026-01-17', 103, 0.00,    'USD'),
(4, '2026-01-18', 104, 7800.00, 'EUR'),
(5, NULL,         105, 1500.00, 'USD'),
(6, '2026-01-20', 106, 9200.75, 'USD'),
(7, '2026-01-21', 107, 0.00,    'EUR'),
(8, '2026-01-22', 108, 4300.00, 'USD'),
(9, NULL,         109, 2100.00, 'EUR'),
(10,'2026-01-24', 110, 6700.00, 'USD');

-- DESTINO: vacía por ahora, es donde el ETL va a escribir lo limpio
CREATE DATABASE IF NOT EXISTS etl_destino;