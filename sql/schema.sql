-- ============================================================
-- Electronic Voting System - Pakistan Style
-- Database Schema with Full Normalization
-- ============================================================

CREATE DATABASE IF NOT EXISTS evs_pakistan;
USE evs_pakistan;

-- ============================================================
-- ADMINS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL
);

-- ============================================================
-- CONSTITUENCIES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS constituencies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(20) UNIQUE NOT NULL,          -- e.g. NA-109, PP-113
    election_type ENUM('national', 'provincial') NOT NULL,
    province VARCHAR(50),
    description VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_type (election_type)
);

-- ============================================================
-- VOTERS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS voters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cnic VARCHAR(15) UNIQUE NOT NULL,          -- Format: XXXXX-XXXXXXX-X
    full_name VARCHAR(100) NOT NULL,
    city VARCHAR(50) NOT NULL,
    na_constituency_id INT,                    -- National Assembly
    pp_constituency_id INT,                    -- Provincial Assembly
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP NULL,
    approved_by INT NULL,
    FOREIGN KEY (na_constituency_id) REFERENCES constituencies(id) ON DELETE SET NULL,
    FOREIGN KEY (pp_constituency_id) REFERENCES constituencies(id) ON DELETE SET NULL,
    FOREIGN KEY (approved_by) REFERENCES admins(id) ON DELETE SET NULL,
    INDEX idx_status (status),
    INDEX idx_cnic (cnic)
);

-- ============================================================
-- CANDIDATES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS candidates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    party_name VARCHAR(100) NOT NULL,
    party_symbol_path VARCHAR(255),            -- path to symbol image
    constituency_id INT NOT NULL,
    election_type ENUM('national', 'provincial') NOT NULL,
    bio TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (constituency_id) REFERENCES constituencies(id) ON DELETE CASCADE,
    INDEX idx_constituency (constituency_id),
    INDEX idx_election_type (election_type)
);

-- ============================================================
-- ELECTION SCHEDULE TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS election_schedule (
    id INT AUTO_INCREMENT PRIMARY KEY,
    election_type ENUM('national', 'provincial', 'both') NOT NULL,
    constituency_id INT NULL,                  -- NULL = applies to all
    start_datetime DATETIME NOT NULL,
    end_datetime DATETIME NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (constituency_id) REFERENCES constituencies(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES admins(id) ON DELETE SET NULL
);

-- ============================================================
-- VOTES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS votes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    voter_id INT NOT NULL,
    candidate_id INT NOT NULL,
    constituency_id INT NOT NULL,
    election_type ENUM('national', 'provincial') NOT NULL,
    voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (voter_id) REFERENCES voters(id) ON DELETE CASCADE,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
    FOREIGN KEY (constituency_id) REFERENCES constituencies(id) ON DELETE CASCADE,
    -- Prevent duplicate voting: one vote per voter per election type
    UNIQUE KEY unique_voter_election (voter_id, election_type),
    INDEX idx_candidate (candidate_id),
    INDEX idx_constituency (constituency_id)
);

-- ============================================================
-- AUDIT LOGS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_type ENUM('admin', 'voter') NOT NULL,
    user_id INT NOT NULL,
    action VARCHAR(100) NOT NULL,
    details TEXT,
    ip_address VARCHAR(45),
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user (user_type, user_id),
    INDEX idx_action (action)
);

-- ============================================================
-- RESULTS VIEW (Virtual)
-- ============================================================
CREATE OR REPLACE VIEW results_view AS
SELECT 
    c.id AS candidate_id,
    c.full_name AS candidate_name,
    c.party_name,
    c.party_symbol_path,
    con.name AS constituency_name,
    c.election_type,
    COUNT(v.id) AS vote_count
FROM candidates c
LEFT JOIN constituencies con ON c.constituency_id = con.id
LEFT JOIN votes v ON v.candidate_id = c.id
WHERE c.is_active = TRUE
GROUP BY c.id, c.full_name, c.party_name, c.party_symbol_path, con.name, c.election_type;

-- ============================================================
-- SAMPLE DATA
-- ============================================================

-- Admin account (password: Admin@123)
INSERT INTO admins (username, password_hash, full_name, email) VALUES
('admin', '$2b$12$vBZwQS2sKlG6HBO1c6Q9VuGCxgXCqY2odTVVjkQQPVJfQ9O5AsSu2', 'System Administrator', 'admin@evs.gov.pk');

-- National Assembly Constituencies
INSERT INTO constituencies (name, election_type, province, description) VALUES
('NA-109', 'national', 'Punjab', 'Lahore Division - Central'),
('NA-110', 'national', 'Punjab', 'Lahore Division - East'),
('NA-111', 'national', 'Punjab', 'Lahore Division - West'),
('NA-112', 'national', 'Punjab', 'Lahore Division - North'),
('NA-113', 'national', 'Sindh', 'Karachi Central'),
('NA-114', 'national', 'Sindh', 'Karachi East'),
('NA-115', 'national', 'KPK', 'Peshawar Division'),
('NA-116', 'national', 'Balochistan', 'Quetta Division');

-- Provincial Assembly Constituencies
INSERT INTO constituencies (name, election_type, province, description) VALUES
('PP-113', 'provincial', 'Punjab', 'Lahore - Model Town'),
('PP-114', 'provincial', 'Punjab', 'Lahore - Gulberg'),
('PP-115', 'provincial', 'Punjab', 'Lahore - Johar Town'),
('PP-116', 'provincial', 'Punjab', 'Lahore - Cantt'),
('PS-113', 'provincial', 'Sindh', 'Karachi Central'),
('PS-114', 'provincial', 'Sindh', 'Karachi East'),
('PK-113', 'provincial', 'KPK', 'Peshawar Central'),
('PB-113', 'provincial', 'Balochistan', 'Quetta Central');

-- Sample Candidates for NA-109
INSERT INTO candidates (full_name, party_name, constituency_id, election_type, bio) VALUES
('Shahid Malik', 'Pakistan Tehreek-e-Insaf', 1, 'national', 'Experienced politician with 15 years in public service'),
('Hamid Raza', 'Pakistan Muslim League (N)', 1, 'national', 'Former MNA, focused on education and healthcare'),
('Farooq Ahmed', 'Pakistan Peoples Party', 1, 'national', 'Businessman turned politician'),
('Tariq Mahmood', 'Muttahida Qaumi Movement', 1, 'national', 'Youth leader and social activist');

-- Sample Candidates for NA-110
INSERT INTO candidates (full_name, party_name, constituency_id, election_type, bio) VALUES
('Zubair Khan', 'Pakistan Tehreek-e-Insaf', 2, 'national', 'Engineer and development expert'),
('Nasir Javed', 'Pakistan Muslim League (N)', 2, 'national', 'Local businessman supporting infrastructure'),
('Amina Bibi', 'Pakistan Peoples Party', 2, 'national', 'First female candidate in this constituency');

-- Sample Candidates for PP-113
INSERT INTO candidates (full_name, party_name, constituency_id, election_type, bio) VALUES
('Rashid Ali', 'Pakistan Tehreek-e-Insaf', 9, 'provincial', 'Former city councilor'),
('Bilal Hassan', 'Pakistan Muslim League (N)', 9, 'provincial', 'Education sector reformer'),
('Sajida Bano', 'Pakistan Peoples Party', 9, 'provincial', 'Social worker and community leader'),
('Arif Chattha', 'Jamaat-e-Islami', 9, 'provincial', 'Religious scholar and educator');

-- Sample Candidates for PP-114
INSERT INTO candidates (full_name, party_name, constituency_id, election_type, bio) VALUES
('Kamran Shafi', 'Pakistan Tehreek-e-Insaf', 10, 'provincial', 'IT professional turned politician'),
('Usman Dar', 'Pakistan Muslim League (N)', 10, 'provincial', 'Former deputy commissioner'),
('Rukhsana Kausar', 'Pakistan Peoples Party', 10, 'provincial', 'Womens rights activist');

-- Election Schedule (active election)
INSERT INTO election_schedule (election_type, start_datetime, end_datetime, is_active) VALUES
('both', DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_ADD(NOW(), INTERVAL 2 DAY), TRUE);

-- Sample approved voters (password: Voter@123)
INSERT INTO voters (cnic, full_name, city, na_constituency_id, pp_constituency_id, username, password_hash, status) VALUES
('35202-1234567-1', 'Ahmed Hassan', 'Lahore', 1, 9, 'ahmed_hassan', '$2b$12$GSNVzPFI3dmjvUo7Gi1u.u7X/VvCumvtEUARBhSePn06qI6gL10rO', 'approved'),
('35202-2345678-2', 'Fatima Noor', 'Lahore', 1, 9, 'fatima_noor', '$2b$12$GSNVzPFI3dmjvUo7Gi1u.u7X/VvCumvtEUARBhSePn06qI6gL10rO', 'approved'),
('35202-3456789-3', 'Usman Ali', 'Lahore', 2, 10, 'usman_ali', '$2b$12$GSNVzPFI3dmjvUo7Gi1u.u7X/VvCumvtEUARBhSePn06qI6gL10rO', 'approved'),
('35202-4567890-4', 'Sara Khan', 'Lahore', 2, 10, 'sara_khan', '$2b$12$GSNVzPFI3dmjvUo7Gi1u.u7X/VvCumvtEUARBhSePn06qI6gL10rO', 'pending'),
('35202-5678901-5', 'Bilal Asif', 'Lahore', 1, 9, 'bilal_asif', '$2b$12$GSNVzPFI3dmjvUo7Gi1u.u7X/VvCumvtEUARBhSePn06qI6gL10rO', 'pending');
