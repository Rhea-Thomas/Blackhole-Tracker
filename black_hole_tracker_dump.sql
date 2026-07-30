
-- BLACK HOLE OBSERVATION TRACKER DATABASE DUMP --
-- Author: Rhea Thomas
-- Date: December 2024
-- Database: PostgreSQL 12+
-- Purpose: Complete database schema and data for Black Hole Observation Tracker
--
-- This dump file contains:
-- 1. Seven (7) normalized tables in 3rd Normal Form (3NF)
-- 2. Primary and foreign key constraints with CASCADE operations
-- 3. User-defined functions (stored procedures)
-- 4. Database triggers for audit logging
-- 5. Database event functions for scheduled cleanup
-- 6. Secondary indexes with performance justifications
-- 7. Sample data for evaluation


-- Drop existing database objects to ensure clean installation
DROP TABLE IF EXISTS audit_log CASCADE;
DROP TABLE IF EXISTS saved_dashboards CASCADE;
DROP TABLE IF EXISTS observations CASCADE;
DROP TABLE IF EXISTS gravitational_wave_events CASCADE;
DROP TABLE IF EXISTS black_holes CASCADE;
DROP TABLE IF EXISTS observatories CASCADE;
DROP TABLE IF EXISTS observation_types CASCADE;
DROP TABLE IF EXISTS wavelength_ranges CASCADE;
DROP TABLE IF EXISTS discovery_methods CASCADE;

DROP FUNCTION IF EXISTS get_most_observed_bh(INT) CASCADE;
DROP FUNCTION IF EXISTS get_avg_intensity_per_bh() CASCADE;
DROP FUNCTION IF EXISTS get_observations_by_type() CASCADE;
DROP FUNCTION IF EXISTS audit_trigger_func() CASCADE;
DROP FUNCTION IF EXISTS cleanup_old_audit_logs() CASCADE;


-- TABLE DEFINITIONS (3rd Normal Form)

-- ----------------------------------------------------------------------------
-- Table: discovery_methods
-- Purpose: Lookup table for black hole discovery methods
-- Normalization: 3NF - No transitive dependencies, atomic values
-- ----------------------------------------------------------------------------
CREATE TABLE discovery_methods (
    method_id SERIAL PRIMARY KEY,
    method_name VARCHAR(100) NOT NULL UNIQUE,
    year_developed INT NOT NULL,
    description TEXT,
    CONSTRAINT chk_year_developed CHECK (year_developed >= 1600 AND year_developed <= 2025)
);

COMMENT ON TABLE discovery_methods IS 'Catalog of methods used to discover black holes';
COMMENT ON COLUMN discovery_methods.year_developed IS 'Year the discovery method was first developed';

-- ----------------------------------------------------------------------------
-- Table: observation_types
-- Purpose: Lookup table for types of astronomical observations
-- Normalization: 3NF - Separates observation type attributes from observations
-- ----------------------------------------------------------------------------
CREATE TABLE observation_types (
    type_id SERIAL PRIMARY KEY,
    type_name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    wavelength_range VARCHAR(100),
    CONSTRAINT chk_type_name_not_empty CHECK (type_name != '')
);

COMMENT ON TABLE observation_types IS 'Categories of astronomical observations (X-ray, Radio, Optical, etc.)';

-- ----------------------------------------------------------------------------
-- Table: wavelength_ranges
-- Purpose: Electromagnetic spectrum ranges for observations
-- Normalization: 3NF - Removes wavelength details from observations table
-- ----------------------------------------------------------------------------
CREATE TABLE wavelength_ranges (
    wavelength_id SERIAL PRIMARY KEY,
    wavelength_name VARCHAR(50) NOT NULL UNIQUE,
    min_wavelength FLOAT NOT NULL,
    max_wavelength FLOAT NOT NULL,
    unit VARCHAR(20) NOT NULL DEFAULT 'nm',
    CONSTRAINT chk_wavelength_positive CHECK (min_wavelength > 0 AND max_wavelength > 0),
    CONSTRAINT chk_wavelength_order CHECK (min_wavelength < max_wavelength)
);

COMMENT ON TABLE wavelength_ranges IS 'Electromagnetic spectrum wavelength ranges';
COMMENT ON CONSTRAINT chk_wavelength_order ON wavelength_ranges IS 'Ensures minimum wavelength is less than maximum';

-- ----------------------------------------------------------------------------
-- Table: observatories
-- Purpose: Astronomical facilities that conduct observations
-- Normalization: 3NF - Independent entity with no redundant data
-- ----------------------------------------------------------------------------
CREATE TABLE observatories (
    observatory_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    location VARCHAR(100),
    type VARCHAR(50),
    operational_since INT,
    CONSTRAINT chk_operational_since CHECK (operational_since >= 1600 AND operational_since <= 2025)
);

COMMENT ON TABLE observatories IS 'Telescope facilities and observatories worldwide';
COMMENT ON COLUMN observatories.type IS 'Type of observatory: X-ray, Radio, Optical, Gravitational Wave, etc.';

-- ----------------------------------------------------------------------------
-- Table: black_holes
-- Purpose: Core entity representing black holes
-- Normalization: 3NF - All non-key attributes depend only on primary key
-- Relationships: References discovery_methods (many-to-one)
-- ----------------------------------------------------------------------------
CREATE TABLE black_holes (
    bh_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    mass_solar_masses FLOAT,
    distance_light_years FLOAT,
    classification VARCHAR(50),
    discovery_year INT,
    discovery_method_id INT,
    ra FLOAT, -- Right Ascension (0-360 degrees)
    dec FLOAT, -- Declination (-90 to +90 degrees)
    
    -- Foreign key with CASCADE to maintain referential integrity
    CONSTRAINT fk_discovery_method 
        FOREIGN KEY (discovery_method_id) 
        REFERENCES discovery_methods(method_id) 
        ON DELETE SET NULL 
        ON UPDATE CASCADE,
    
    -- Domain constraints
    CONSTRAINT chk_mass_positive CHECK (mass_solar_masses > 0),
    CONSTRAINT chk_distance_positive CHECK (distance_light_years > 0),
    CONSTRAINT chk_discovery_year CHECK (discovery_year >= 1600 AND discovery_year <= 2025),
    CONSTRAINT chk_ra_range CHECK (ra >= 0 AND ra <= 360),
    CONSTRAINT chk_dec_range CHECK (dec >= -90 AND dec <= 90),
    CONSTRAINT chk_name_not_empty CHECK (name != '')
);

COMMENT ON TABLE black_holes IS 'Catalog of discovered black holes with physical properties';
COMMENT ON COLUMN black_holes.mass_solar_masses IS 'Mass in units of solar masses (M☉)';
COMMENT ON COLUMN black_holes.distance_light_years IS 'Distance from Earth in light-years';
COMMENT ON COLUMN black_holes.classification IS 'Stellar, Intermediate, Supermassive, or Primordial';
COMMENT ON COLUMN black_holes.ra IS 'Right Ascension coordinate (0-360°)';
COMMENT ON COLUMN black_holes.dec IS 'Declination coordinate (-90° to +90°)';

-- ----------------------------------------------------------------------------
-- Table: observations
-- Purpose: Junction table linking black holes to observatories with observation data
-- Normalization: 3NF - Represents many-to-many relationship with additional attributes
-- Relationships: References black_holes, observatories, observation_types, wavelength_ranges
-- ----------------------------------------------------------------------------
CREATE TABLE observations (
    obs_id SERIAL PRIMARY KEY,
    bh_id INT NOT NULL,
    observatory_id INT NOT NULL,
    observation_date DATE NOT NULL,
    type_id INT,
    wavelength_id INT,
    intensity FLOAT,
    notes TEXT,
    
    -- Foreign keys with CASCADE operations
    CONSTRAINT fk_black_hole 
        FOREIGN KEY (bh_id) 
        REFERENCES black_holes(bh_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
        
    CONSTRAINT fk_observatory 
        FOREIGN KEY (observatory_id) 
        REFERENCES observatories(observatory_id) 
        ON DELETE SET NULL 
        ON UPDATE CASCADE,
        
    CONSTRAINT fk_observation_type 
        FOREIGN KEY (type_id) 
        REFERENCES observation_types(type_id) 
        ON DELETE SET NULL 
        ON UPDATE CASCADE,
        
    CONSTRAINT fk_wavelength_range 
        FOREIGN KEY (wavelength_id) 
        REFERENCES wavelength_ranges(wavelength_id) 
        ON DELETE SET NULL 
        ON UPDATE CASCADE,
    
    -- Domain constraints
    CONSTRAINT chk_intensity_nonnegative CHECK (intensity >= 0),
    CONSTRAINT chk_observation_date_not_future CHECK (observation_date <= CURRENT_DATE)
);

COMMENT ON TABLE observations IS 'Records of telescope observations of black holes';
COMMENT ON COLUMN observations.intensity IS 'Measured intensity of observation (arbitrary units)';
COMMENT ON CONSTRAINT fk_black_hole ON observations IS 'CASCADE delete ensures observations are removed when black hole is deleted';
COMMENT ON CONSTRAINT fk_observatory ON observations IS 'SET NULL allows observations to remain if observatory is removed';

-- ----------------------------------------------------------------------------
-- Table: gravitational_wave_events
-- Purpose: Records of black hole merger events detected by gravitational wave observatories
-- Normalization: 3NF - Separate entity for merger events with their unique properties
-- Relationships: References black_holes twice (self-referencing for merger pairs)
-- ----------------------------------------------------------------------------
CREATE TABLE gravitational_wave_events (
    gw_event_id SERIAL PRIMARY KEY,
    event_name VARCHAR(100) NOT NULL,
    bh1_id INT NOT NULL,
    bh2_id INT NOT NULL,
    event_date DATE NOT NULL,
    mass_1 FLOAT,
    mass_2 FLOAT,
    final_mass FLOAT,
    energy_released FLOAT,
    
    -- Foreign keys for the two merging black holes
    CONSTRAINT fk_black_hole_1 
        FOREIGN KEY (bh1_id) 
        REFERENCES black_holes(bh_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
        
    CONSTRAINT fk_black_hole_2 
        FOREIGN KEY (bh2_id) 
        REFERENCES black_holes(bh_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    
    -- Domain constraints
    CONSTRAINT chk_masses_positive CHECK (mass_1 > 0 AND mass_2 > 0 AND final_mass > 0),
    CONSTRAINT chk_energy_positive CHECK (energy_released > 0),
    CONSTRAINT chk_different_black_holes CHECK (bh1_id != bh2_id),
    CONSTRAINT chk_event_date_not_future CHECK (event_date <= CURRENT_DATE)
);

COMMENT ON TABLE gravitational_wave_events IS 'Detected black hole merger events (e.g., LIGO/Virgo detections)';
COMMENT ON COLUMN gravitational_wave_events.event_name IS 'Official designation (e.g., GW150914)';
COMMENT ON COLUMN gravitational_wave_events.energy_released IS 'Energy released in solar masses (E=mc²)';
COMMENT ON CONSTRAINT chk_different_black_holes ON gravitational_wave_events IS 'Prevents a black hole from merging with itself';

-- ----------------------------------------------------------------------------
-- Table: saved_dashboards
-- Purpose: Stores user-created custom dashboard configurations
-- Normalization: 3NF - Independent entity for dashboard metadata
-- ----------------------------------------------------------------------------
CREATE TABLE saved_dashboards (
    dashboard_id SERIAL PRIMARY KEY,
    dashboard_name VARCHAR(200) NOT NULL,
    report_type VARCHAR(100) NOT NULL,
    bh_id INT,
    observatory_id INT,
    obs_type_id INT,
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    
    CONSTRAINT chk_dashboard_name_not_empty CHECK (dashboard_name != ''),
    CONSTRAINT chk_date_range CHECK (start_date IS NULL OR end_date IS NULL OR start_date <= end_date)
);

COMMENT ON TABLE saved_dashboards IS 'User-created custom dashboard configurations';
COMMENT ON COLUMN saved_dashboards.report_type IS 'Type of report: observations_by_bh, observations_by_observatory, etc.';

-- ----------------------------------------------------------------------------
-- Table: audit_log
-- Purpose: Automatically tracks all UPDATE and DELETE operations on critical tables
-- Normalization: 3NF - Separate audit trail entity
-- Note: Populated automatically by database triggers
-- ----------------------------------------------------------------------------
CREATE TABLE audit_log (
    audit_id SERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    record_id INT,
    old_data TEXT,
    new_data TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by VARCHAR(50) DEFAULT 'system',
    
    CONSTRAINT chk_operation_type CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE'))
);

COMMENT ON TABLE audit_log IS 'Automatic audit trail of all data modifications';
COMMENT ON COLUMN audit_log.old_data IS 'JSON representation of row before change';
COMMENT ON COLUMN audit_log.new_data IS 'JSON representation of row after change';


-- SECONDARY INDEXES (Performance Optimization)
-- Index: idx_observations_bh_id
-- Purpose: Optimize queries filtering/joining observations by black hole
-- Justification: observations.bh_id is frequently used in WHERE clauses and
--                JOIN conditions when retrieving all observations for a 
--                specific black hole. This is the most common query pattern.
-- Expected Improvement: O(log n) lookup vs O(n) table scan

CREATE INDEX idx_observations_bh_id ON observations(bh_id);


-- Index: idx_observations_observatory_id
-- Purpose: Optimize queries filtering by observatory
-- Justification: Used in dashboard reports showing observations per observatory
--                and when filtering observations by facility. This supports
--                the "Observations by Observatory" report.
-- Expected Improvement: Speeds up GROUP BY and JOIN operations on observatory_id

CREATE INDEX idx_observations_observatory_id ON observations(observatory_id);


-- Index: idx_observations_date
-- Purpose: Optimize date-range queries on observations
-- Justification: The custom dashboard builder allows filtering by date range.
--                Without this index, range queries would require full table scans.
--                This is critical for time-series analysis and reporting.
-- Expected Improvement: Enables efficient BETWEEN queries and ORDER BY date
-- ----------------------------------------------------------------------------
CREATE INDEX idx_observations_date ON observations(observation_date);

-- ----------------------------------------------------------------------------
-- Index: idx_observations_type_id
-- Purpose: Optimize queries grouping observations by type
-- Justification: Supports the "Observations by Type" report which groups and
--                counts observations by their type (X-ray, Radio, etc.).
--                Also used in dashboard filtering by observation type.
-- Expected Improvement: Speeds up GROUP BY type_id queries significantly
-- ----------------------------------------------------------------------------
CREATE INDEX idx_observations_type_id ON observations(type_id);

-- ----------------------------------------------------------------------------
-- Index: idx_black_holes_classification
-- Purpose: Optimize search by black hole classification
-- Justification: The search functionality allows filtering by classification
--                (Stellar, Supermassive, etc.). This is a common query pattern
--                in astronomical research when comparing black hole types.
-- Expected Improvement: Enables fast filtering and grouping by classification
-- ----------------------------------------------------------------------------
CREATE INDEX idx_black_holes_classification ON black_holes(classification);

-- ----------------------------------------------------------------------------
-- Index: idx_black_holes_name
-- Purpose: Optimize text search on black hole names
-- Justification: The search feature uses ILIKE queries on names for partial
--                matching (e.g., searching "Cygnus"). PostgreSQL's B-tree index
--                supports pattern matching for prefix searches.
-- Expected Improvement: Speeds up LIKE/ILIKE searches with leading characters
-- ----------------------------------------------------------------------------
CREATE INDEX idx_black_holes_name ON black_holes(name);

-- ----------------------------------------------------------------------------
-- Index: idx_audit_log_date
-- Purpose: Optimize audit log queries by date
-- Justification: The cleanup_old_audit_logs() function filters by date to
--                remove old entries. Also supports audit trail queries by
--                date range for compliance and debugging.
-- Expected Improvement: Makes the periodic cleanup function efficient even
--                      as audit log grows large over time
-- ----------------------------------------------------------------------------
CREATE INDEX idx_audit_log_date ON audit_log(changed_at);

-- USER-DEFINED FUNCTIONS (Stored Procedures)

-- ----------------------------------------------------------------------------
-- Function: get_most_observed_bh
-- Purpose: Returns black holes ranked by observation count
-- Parameters: p_limit (default 5) - number of results to return
-- Used by: Reports page for "Most Observed Black Holes" report
-- Performance: Uses LEFT JOIN to include black holes with zero observations
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION get_most_observed_bh(p_limit INT DEFAULT 5)
RETURNS TABLE (bh_name VARCHAR, observation_count BIGINT) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        b.name AS bh_name,
        COUNT(o.obs_id) AS observation_count
    FROM black_holes b
    LEFT JOIN observations o ON b.bh_id = o.bh_id
    GROUP BY b.bh_id, b.name
    ORDER BY observation_count DESC
    LIMIT p_limit;
END;
$$;

COMMENT ON FUNCTION get_most_observed_bh IS 'Returns top N most frequently observed black holes';

-- ----------------------------------------------------------------------------
-- Function: get_avg_intensity_per_bh
-- Purpose: Calculates average observation intensity for each black hole
-- Used by: Reports page for intensity analysis
-- Note: Excludes black holes with no observations (WHERE clause)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION get_avg_intensity_per_bh()
RETURNS TABLE (bh_name VARCHAR, avg_intensity NUMERIC) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        b.name AS bh_name,
        AVG(o.intensity)::NUMERIC AS avg_intensity
    FROM black_holes b
    LEFT JOIN observations o ON b.bh_id = o.bh_id
    WHERE o.intensity IS NOT NULL
    GROUP BY b.bh_id, b.name
    ORDER BY avg_intensity DESC;
END;
$$;

COMMENT ON FUNCTION get_avg_intensity_per_bh IS 'Calculates average observation intensity per black hole';

-- ----------------------------------------------------------------------------
-- Function: get_observations_by_type
-- Purpose: Groups observations by type with counts
-- Used by: Reports page for "Observations by Type" distribution
-- Performance: LEFT JOIN ensures all observation types appear even with 0 counts
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION get_observations_by_type()
RETURNS TABLE (type_name VARCHAR, observation_count BIGINT) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ot.type_name,
        COUNT(o.obs_id) AS observation_count
    FROM observation_types ot
    LEFT JOIN observations o ON ot.type_id = o.type_id
    GROUP BY ot.type_id, ot.type_name
    ORDER BY observation_count DESC;
END;
$$;

COMMENT ON FUNCTION get_observations_by_type IS 'Returns observation count grouped by observation type';

-- DATABASE TRIGGERS (Automatic Audit Logging)

-- ----------------------------------------------------------------------------
-- Trigger Function: audit_trigger_func
-- Purpose: Automatically logs all UPDATE and DELETE operations to audit_log
-- Fired by: Triggers on black_holes and observations tables
-- Design: Generic function that works with any table via TG_* variables
-- Note: Uses row_to_json() to capture complete row state
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER 
LANGUAGE plpgsql
AS $$
BEGIN
    -- Handle DELETE operations
    IF (TG_OP = 'DELETE') THEN
        INSERT INTO audit_log (table_name, operation, record_id, old_data)
        VALUES (
            TG_TABLE_NAME,
            TG_OP,
            OLD.bh_id,  -- Assumes bh_id exists (works for black_holes table)
            row_to_json(OLD)::TEXT
        );
        RETURN OLD;
    
    -- Handle UPDATE operations
    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO audit_log (table_name, operation, record_id, old_data, new_data)
        VALUES (
            TG_TABLE_NAME,
            TG_OP,
            NEW.bh_id,  -- Assumes bh_id exists
            row_to_json(OLD)::TEXT,
            row_to_json(NEW)::TEXT
        );
        RETURN NEW;
    END IF;
    
    RETURN NULL;
END;
$$;

COMMENT ON FUNCTION audit_trigger_func IS 'Generic trigger function for audit logging';

-- Create triggers on critical tables
DROP TRIGGER IF EXISTS black_holes_audit_trigger ON black_holes;
CREATE TRIGGER black_holes_audit_trigger
    AFTER UPDATE OR DELETE ON black_holes
    FOR EACH ROW 
    EXECUTE FUNCTION audit_trigger_func();

DROP TRIGGER IF EXISTS observations_audit_trigger ON observations;
CREATE TRIGGER observations_audit_trigger
    AFTER UPDATE OR DELETE ON observations
    FOR EACH ROW 
    EXECUTE FUNCTION audit_trigger_func();

COMMENT ON TRIGGER black_holes_audit_trigger ON black_holes IS 'Automatically logs all changes to black_holes table';
COMMENT ON TRIGGER observations_audit_trigger ON observations IS 'Automatically logs all changes to observations table';

-- DATABASE EVENT FUNCTION (Scheduled Maintenance)

-- ----------------------------------------------------------------------------
-- Function: cleanup_old_audit_logs
-- Purpose: Removes audit log entries older than 90 days
-- Usage: Designed to be called by pg_cron or scheduled job
-- Schedule: Recommended weekly execution
-- Note: In production, schedule with:
--       SELECT cron.schedule('cleanup-audit-logs', '0 0 * * 0', 
--                            'SELECT cleanup_old_audit_logs()');
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION cleanup_old_audit_logs()
RETURNS void 
LANGUAGE plpgsql
AS $$
DECLARE
    deleted_count INT;
BEGIN
    DELETE FROM audit_log 
    WHERE changed_at < NOW() - INTERVAL '90 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RAISE NOTICE 'Cleanup completed: % audit log entries deleted', deleted_count;
END;
$$;

COMMENT ON FUNCTION cleanup_old_audit_logs IS 'Scheduled cleanup function to maintain audit log size';

-- SAMPLE DATA INSERTION

-- Discovery Methods
INSERT INTO discovery_methods (method_name, year_developed, description) VALUES
    ('Radio Telescope', 1930, 'Detection via radio frequency signals'),
    ('X-ray Telescope', 1960, 'Detection via X-ray emissions'),
    ('Optical Telescope', 1600, 'Detection via visible light'),
    ('Gravitational Wave Detection', 2015, 'Detection via LIGO/Virgo interferometers'),
    ('Infrared Telescope', 1970, 'Detection via infrared radiation');

-- Observation Types
INSERT INTO observation_types (type_name, description, wavelength_range) VALUES
    ('X-ray', 'High energy electromagnetic radiation', '0.01nm - 10nm'),
    ('Radio', 'Low frequency electromagnetic radiation', '1mm - 1m'),
    ('Optical', 'Visible light spectrum', '400nm - 700nm'),
    ('Infrared', 'Heat radiation', '700nm - 1mm'),
    ('Gravitational Wave', 'Ripples in spacetime fabric', 'N/A');

-- Wavelength Ranges
INSERT INTO wavelength_ranges (wavelength_name, min_wavelength, max_wavelength, unit) VALUES
    ('X-ray', 0.01, 10.0, 'nm'),
    ('Ultraviolet', 10.0, 400.0, 'nm'),
    ('Visible', 400.0, 700.0, 'nm'),
    ('Infrared', 700.0, 1000000.0, 'nm'),
    ('Microwave', 1000000.0, 1000000000.0, 'nm'),
    ('Radio', 1000000000.0, 1000000000000.0, 'nm');

-- Observatories
INSERT INTO observatories (name, location, type, operational_since) VALUES
    ('Chandra X-ray Observatory', 'Space', 'X-ray', 1999),
    ('Event Horizon Telescope', 'Global', 'Radio', 2015),
    ('LIGO', 'USA', 'Gravitational Wave', 2015),
    ('Virgo', 'Italy', 'Gravitational Wave', 2007),
    ('Hubble Space Telescope', 'Space', 'Optical', 1990),
    ('NuSTAR', 'Space', 'X-ray', 2012);

-- Black Holes (Mix of stellar and supermassive)
INSERT INTO black_holes (name, mass_solar_masses, distance_light_years, classification, discovery_year, discovery_method_id, ra, dec) VALUES
    ('Cygnus X-1', 14.8, 6070, 'Stellar', 1964, 1, 299.590, 35.202),
    ('M87*', 6500000000, 53000000, 'Supermassive', 2019, 2, 187.706, 12.391),
    ('Sagittarius A*', 4000000, 26000, 'Supermassive', 1974, 1, 266.417, -29.008),
    ('TON 618', 66000000000, 18200000000, 'Supermassive', 1957, 1, 53.100, 1.537),
    ('ULAS J1342+0928', 800000000, 13100000000, 'Supermassive', 2017, 2, 205.600, 9.342),
    ('V404 Cygni', 9.0, 7800, 'Stellar', 1989, 1, 306.019, 33.534),
    ('GRS 1915+105', 12.0, 36000, 'Stellar', 1992, 1, 288.798, 11.156),
    ('Mrk 421', 300000000, 400000000, 'Supermassive', 1966, 1, 166.114, 38.209);

-- Observations (Sample data showing various observation patterns)
-- Cygnus X-1 observations
INSERT INTO observations (bh_id, observatory_id, observation_date, type_id, wavelength_id, intensity, notes) VALUES
    (1, 1, '2024-01-15', 1, 1, 45.3, 'Strong X-ray emission detected'),
    (1, 2, '2024-02-20', 2, 6, 32.1, 'Radio flare observed'),
    (1, 5, '2024-03-10', 3, 3, 28.7, 'Optical counterpart confirmed'),
    (1, 1, '2024-04-05', 1, 1, 51.2, 'Increased X-ray activity'),
    (1, 6, '2024-05-22', 1, 1, 38.9, 'NuSTAR observation campaign');

-- M87* observations (famously imaged by EHT)
INSERT INTO observations (bh_id, observatory_id, observation_date, type_id, wavelength_id, intensity, notes) VALUES
    (2, 2, '2024-01-08', 2, 6, 89.4, 'Event Horizon Telescope imaging'),
    (2, 2, '2024-02-15', 2, 6, 92.1, 'Follow-up EHT observation'),
    (2, 1, '2024-03-20', 1, 1, 67.8, 'X-ray jet emission'),
    (2, 5, '2024-04-12', 3, 3, 41.2, 'Optical jet detected');

-- Sagittarius A* observations (Milky Way center)
INSERT INTO observations (bh_id, observatory_id, observation_date, type_id, wavelength_id, intensity, notes) VALUES
    (3, 1, '2024-01-20', 1, 1, 72.5, 'Flare event observed'),
    (3, 2, '2024-02-28', 2, 6, 55.3, 'Radio monitoring'),
    (3, 5, '2024-03-15', 4, 4, 61.7, 'Infrared stellar motion'),
    (3, 6, '2024-04-08', 1, 1, 68.2, 'Hard X-ray detection'),
    (3, 2, '2024-05-18', 2, 6, 58.9, 'VLBI observation'),
    (3, 1, '2024-06-25', 1, 1, 75.1, 'Extended flare activity');

-- TON 618 observations (Most massive known black hole)
INSERT INTO observations (bh_id, observatory_id, observation_date, type_id, wavelength_id, intensity, notes) VALUES
    (4, 5, '2024-01-10', 3, 3, 95.6, 'Quasar optical spectrum'),
    (4, 2, '2024-03-05', 2, 6, 88.3, 'Radio jet structure'),
    (4, 1, '2024-05-20', 1, 1, 91.2, 'X-ray emission from accretion disk');

-- ULAS J1342+0928 observations
INSERT INTO observations (bh_id, observatory_id, observation_date, type_id, wavelength_id, intensity, notes) VALUES
    (5, 5, '2024-02-12', 4, 4, 78.4, 'High-redshift quasar detection'),
    (5, 2, '2024-04-18', 2, 6, 71.9, 'Radio emission detected');

-- V404 Cygni observations
INSERT INTO observations (bh_id, observatory_id, observation_date, type_id, wavelength_id, intensity, notes) VALUES
    (6, 1, '2024-01-25', 1, 1, 42.7, 'Outburst monitoring'),
    (6, 6, '2024-02-14', 1, 1, 39.5, 'NuSTAR spectral analysis'),
    (6, 2, '2024-03-30', 2, 6, 35.8, 'Radio jets detected'),
    (6, 5, '2024-05-05', 3, 3, 31.2, 'Optical light curves');

-- GRS 1915+105 observations
INSERT INTO observations (bh_id, observatory_id, observation_date, type_id, wavelength_id, intensity, notes) VALUES
    (7, 1, '2024-02-08', 1, 1, 87.3, 'Superluminal jet observation'),
    (7, 2, '2024-03-22', 2, 6, 79.6, 'Radio flare detected'),
    (7, 6, '2024-05-10', 1, 1, 84.1, 'Hard X-ray variability');

-- Mrk 421 observations (Active galactic nucleus)
INSERT INTO observations (bh_id, observatory_id, observation_date, type_id, wavelength_id, intensity, notes) VALUES
    (8, 1, '2024-01-30', 1, 1, 66.5, 'Blazer activity detected'),
    (8, 5, '2024-03-12', 3, 3, 59.3, 'Optical variability'),
    (8, 2, '2024-04-28', 2, 6, 62.8, 'Radio monitoring');

-- Gravitational Wave Events (Famous LIGO/Virgo detections)
INSERT INTO gravitational_wave_events (event_name, bh1_id, bh2_id, event_date, mass_1, mass_2, final_mass, energy_released) VALUES
    ('GW150914', 1, 6, '2015-09-14', 36.0, 29.0, 62.0, 3.0),
    ('GW170814', 1, 7, '2017-08-14', 30.5, 25.3, 53.0, 2.7),
    ('GW190412', 6, 7, '2019-04-12', 29.4, 8.4, 36.1, 1.7);

-- DATA VERIFICATION QUERIES

-- Verify table row counts
SELECT 'discovery_methods' AS table_name, COUNT(*) AS row_count FROM discovery_methods
UNION ALL
SELECT 'observation_types', COUNT(*) FROM observation_types
UNION ALL
SELECT 'wavelength_ranges', COUNT(*) FROM wavelength_ranges
UNION ALL
SELECT 'observatories', COUNT(*) FROM observatories
UNION ALL
SELECT 'black_holes', COUNT(*) FROM black_holes
UNION ALL
SELECT 'observations', COUNT(*) FROM observations
UNION ALL
SELECT 'gravitational_wave_events', COUNT(*) FROM gravitational_wave_events
ORDER BY table_name;

-- Verify foreign key relationships
SELECT 
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    rc.update_rule,
    rc.delete_rule
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
JOIN information_schema.referential_constraints AS rc
  ON tc.constraint_name = rc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
ORDER BY tc.table_name, kcu.column_name;

-- Verify indexes exist
SELECT 
    tablename, 
    indexname, 
    indexdef 
FROM pg_indexes 
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- Test stored procedures
SELECT * FROM get_most_observed_bh(5);
SELECT * FROM get_avg_intensity_per_bh();
SELECT * FROM get_observations_by_type();

