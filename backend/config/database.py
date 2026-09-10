"""
Database Configuration & Initialization for ManganeseInsight
------------------------------------------------------------
Manages MySQL connection pooling and automatic schema initialization using
environment variables (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD).
"""

import os
import pymysql
import json
from typing import Optional, Dict, Any, List
from config.settings import settings

class DatabaseManager:
    """Manages MySQL connections and schema creation."""

    def __init__(self):
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = int(os.getenv("DB_PORT", "3306"))
        self.db_name = os.getenv("DB_NAME", "manganese_insight")
        self.user = os.getenv("DB_USER", "root")
        self.password = os.getenv("DB_PASSWORD", "root")
        self._init_db()

    def get_connection(self):
        """Returns a new connection to the manganese_insight database."""
        return pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.db_name,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )

    def _init_db(self):
        """Creates the database and necessary tables if they do not exist."""
        try:
            # Connect to MySQL server without selecting DB first
            root_conn = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                charset="utf8mb4",
                autocommit=True
            )
            with root_conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{self.db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            root_conn.close()

            # Connect to target DB and create tables
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # 1. Production Predictions Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS `production_predictions` (
                        `id` INT AUTO_INCREMENT PRIMARY KEY,
                        `mine` VARCHAR(100) NOT NULL,
                        `prediction_date` VARCHAR(50) NOT NULL,
                        `target_production` DOUBLE NOT NULL,
                        `predicted_production` DOUBLE NOT NULL,
                        `shortfall` DOUBLE NOT NULL,
                        `shortfall_percentage` DOUBLE NOT NULL,
                        `model1_shortfall` DOUBLE DEFAULT NULL,
                        `model2_soil_moisture` DOUBLE DEFAULT NULL,
                        `model3_rock` VARCHAR(100) DEFAULT NULL,
                        `model4_equipment_loss` DOUBLE DEFAULT NULL,
                        `risk_score` DOUBLE DEFAULT NULL,
                        `risk_level` VARCHAR(20) DEFAULT NULL,
                        `temperature` DOUBLE DEFAULT NULL,
                        `wind_speed` DOUBLE DEFAULT NULL,
                        `humidity` DOUBLE DEFAULT NULL,
                        `precipitation` DOUBLE DEFAULT NULL,
                        `soil_moisture` DOUBLE DEFAULT NULL,
                        `blasting_file_name` VARCHAR(255) DEFAULT NULL,
                        `equipment_file_name` VARCHAR(255) DEFAULT NULL,
                        `historical_data_json` MEDIUMTEXT DEFAULT NULL,
                        `reasons_json` TEXT DEFAULT NULL,
                        `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)

                # 2. Manganese Estimation / Ore Predictions Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS `manganese_predictions` (
                        `id` INT AUTO_INCREMENT PRIMARY KEY,
                        `latitude` DOUBLE NOT NULL,
                        `longitude` DOUBLE NOT NULL,
                        `predicted_class` INT NOT NULL,
                        `probability` DOUBLE NOT NULL,
                        `potential_category` VARCHAR(50) NOT NULL,
                        `blue_b02` DOUBLE DEFAULT NULL,
                        `green_b03` DOUBLE DEFAULT NULL,
                        `red_b04` DOUBLE DEFAULT NULL,
                        `nir_b08` DOUBLE DEFAULT NULL,
                        `swir1_b11` DOUBLE DEFAULT NULL,
                        `swir2_b12` DOUBLE DEFAULT NULL,
                        `ndvi` DOUBLE DEFAULT NULL,
                        `lithology` VARCHAR(100) DEFAULT NULL,
                        `glim_id` VARCHAR(50) DEFAULT NULL,
                        `elevation_mean_m` DOUBLE DEFAULT NULL,
                        `slope_mean_degrees` DOUBLE DEFAULT NULL,
                        `lst_mean_c` DOUBLE DEFAULT NULL,
                        `features_json` MEDIUMTEXT DEFAULT NULL,
                        `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)

                # 3. Production Recommendations Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS `production_recommendations` (
                        `id` INT AUTO_INCREMENT PRIMARY KEY,
                        `prediction_id` INT DEFAULT NULL,
                        `mine` VARCHAR(100) NOT NULL,
                        `recommendation_date` VARCHAR(50) DEFAULT NULL,
                        `target_production` DOUBLE NOT NULL,
                        `predicted_production` DOUBLE NOT NULL,
                        `shortfall_tonnes` DOUBLE NOT NULL,
                        `shortfall_percentage` DOUBLE NOT NULL,
                        `status` VARCHAR(50) NOT NULL,
                        `possible_reasons_json` MEDIUMTEXT DEFAULT NULL,
                        `recommended_actions_json` MEDIUMTEXT DEFAULT NULL,
                        `cards_json` MEDIUMTEXT DEFAULT NULL,
                        `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (`prediction_id`) REFERENCES `production_predictions`(`id`) ON DELETE SET NULL
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)

                # 4. Users Table (Employee Accounts)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS `users` (
                        `id` INT AUTO_INCREMENT PRIMARY KEY,
                        `employee_id` VARCHAR(50) UNIQUE NOT NULL,
                        `name` VARCHAR(100) NOT NULL,
                        `password_hash` VARCHAR(255) NOT NULL,
                        `status` VARCHAR(20) NOT NULL DEFAULT 'INACTIVE',
                        `role` VARCHAR(20) NOT NULL DEFAULT 'USER',
                        `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)

                # 5. Admins Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS `admins` (
                        `id` INT AUTO_INCREMENT PRIMARY KEY,
                        `admin_id` VARCHAR(50) UNIQUE NOT NULL,
                        `name` VARCHAR(100) NOT NULL,
                        `password_hash` VARCHAR(255) NOT NULL,
                        `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)

                # 6. Login Logs Table (Section 8A)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS `login_logs` (
                        `id` INT AUTO_INCREMENT PRIMARY KEY,
                        `user_type` VARCHAR(20) NOT NULL,
                        `identifier` VARCHAR(50) NOT NULL,
                        `status` VARCHAR(20) NOT NULL DEFAULT 'SUCCESS',
                        `login_timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
            conn.close()
            print(f"Database '{self.db_name}' and tables initialized successfully in MySQL!")
        except Exception as e:
            print(f"Notice: MySQL initialization: {e}")

db_manager = DatabaseManager()
