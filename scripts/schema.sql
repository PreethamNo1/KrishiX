-- ==============================================================================
-- KrishiX Database Initialization Schema
-- Database: agrimatch
-- Target: MySQL 8.0+
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS `agrimatch`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `agrimatch`;

-- ------------------------------------------------------------------------------
-- Table: buyers
-- Stores registered commodity buyers with contact info and geolocation
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `buyers` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL,
    `phone` VARCHAR(20) NOT NULL,
    `lat` DECIMAL(10, 7) NOT NULL,
    `lon` DECIMAL(10, 7) NOT NULL,
    `preferred_commodities` VARCHAR(255) DEFAULT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_coords` (`lat`, `lon`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- Sample Seed Data (Karnataka Region)
-- ------------------------------------------------------------------------------
INSERT INTO `buyers` (`name`, `phone`, `lat`, `lon`, `preferred_commodities`)
VALUES
    ('Bengaluru APMC Mandi Buyer 1', '+919888800001', 12.9716, 77.5946, 'Tomato, Onion, Potato'),
    ('Mysuru Agro Traders',          '+919888800002', 12.2958, 76.6394, 'Ragi, Paddy, Coconut'),
    ('Mandya Sugarcane & Grain Hub', '+919888800003', 12.5222, 76.8978, 'Sugarcane, Paddy, Vegetables'),
    ('Hassan Produce Wholesaler',    '+919888800004', 13.0033, 76.1004, 'Potato, Coffee, Cardamom'),
    ('Tumakuru Commodity Exchange',  '+919888800005', 13.3409, 77.1010, 'Groundnut, Coconut, Ragi'),
    ('Shivamogga Arecanut & Crops',  '+919888800006', 13.9299, 75.5681, 'Arecanut, Paddy, Pepper')
ON DUPLICATE KEY UPDATE `name` = VALUES(`name`);

