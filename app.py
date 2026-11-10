from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import psycopg2
from psycopg2 import sql
import random
from datetime import datetime, timedelta
import os

try:  # optional: read settings from a local .env file
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__)
# Secrets and connection settings come from the environment (see .env.example).
# Nothing sensitive is stored in the code.
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or os.urandom(24)

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'database': os.environ.get('DB_NAME', 'black_hole_tracker'),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'port': int(os.environ.get('DB_PORT', '5432')),
}

def get_db_connection():
    """Create and return database connection"""
    conn = psycopg2.connect(**DB_CONFIG)
    return conn

def init_db():
    """Initialize database with schema and sample data"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Drop existing tables if they exist
    cur.execute("DROP TABLE IF EXISTS audit_log CASCADE;")
    cur.execute("DROP TABLE IF EXISTS observations CASCADE;")
    cur.execute("DROP TABLE IF EXISTS gravitational_wave_events CASCADE;")
    cur.execute("DROP TABLE IF EXISTS black_holes CASCADE;")
    cur.execute("DROP TABLE IF EXISTS observatories CASCADE;")
    cur.execute("DROP TABLE IF EXISTS observation_types CASCADE;")
    cur.execute("DROP TABLE IF EXISTS wavelength_ranges CASCADE;")
    cur.execute("DROP TABLE IF EXISTS discovery_methods CASCADE;")
    
    # Drop existing functions if they exist
    cur.execute("DROP FUNCTION IF EXISTS get_most_observed_bh(INT) CASCADE;")
    cur.execute("DROP FUNCTION IF EXISTS get_avg_intensity_per_bh() CASCADE;")
    cur.execute("DROP FUNCTION IF EXISTS get_observations_by_type() CASCADE;")
    cur.execute("DROP FUNCTION IF EXISTS audit_trigger_func() CASCADE;")
    cur.execute("DROP FUNCTION IF EXISTS cleanup_old_audit_logs() CASCADE;")
    
    # Create tables
    cur.execute("""
        CREATE TABLE observation_types (
            type_id SERIAL PRIMARY KEY,
            type_name VARCHAR(50) NOT NULL UNIQUE,
            description TEXT,
            wavelength_range VARCHAR(100)
        );
    """)

    cur.execute("""
        CREATE TABLE wavelength_ranges (
            wavelength_id SERIAL PRIMARY KEY,
            wavelength_name VARCHAR(50) NOT NULL UNIQUE,
            min_wavelength FLOAT,
            max_wavelength FLOAT,
            unit VARCHAR(20)
        );
    """)

    cur.execute("""
        CREATE TABLE discovery_methods (
            method_id SERIAL PRIMARY KEY,
            method_name VARCHAR(100) NOT NULL UNIQUE,
            year_developed INT,
            description TEXT
        );
    """)

    cur.execute("""
        CREATE TABLE observatories (
            observatory_id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            location VARCHAR(100),
            type VARCHAR(50),
            operational_since INT
        );
    """)
    
    cur.execute("""
        CREATE TABLE black_holes (
            bh_id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            mass_solar_masses FLOAT,
            distance_light_years FLOAT,
            classification VARCHAR(50),
            discovery_year INT,
            discovery_method_id INT,
            ra FLOAT,
            dec FLOAT,
            FOREIGN KEY (discovery_method_id) REFERENCES discovery_methods(method_id) ON DELETE SET NULL ON UPDATE CASCADE
        );
    """)
    
    cur.execute("""
        CREATE TABLE observations (
            obs_id SERIAL PRIMARY KEY,
            bh_id INT NOT NULL,
            observatory_id INT NOT NULL,
            observation_date DATE,
            type_id INT,
            wavelength_id INT,
            intensity FLOAT,
            notes TEXT,
            FOREIGN KEY (bh_id) REFERENCES black_holes(bh_id) ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (observatory_id) REFERENCES observatories(observatory_id) ON DELETE SET NULL ON UPDATE CASCADE,
            FOREIGN KEY (type_id) REFERENCES observation_types(type_id) ON DELETE SET NULL ON UPDATE CASCADE,
            FOREIGN KEY (wavelength_id) REFERENCES wavelength_ranges(wavelength_id) ON DELETE SET NULL ON UPDATE CASCADE
        );
    """)
        
    cur.execute("""
        CREATE TABLE gravitational_wave_events (
            gw_event_id SERIAL PRIMARY KEY,
            event_name VARCHAR(100),
            bh1_id INT,
            bh2_id INT,
            event_date DATE,
            mass_1 FLOAT,
            mass_2 FLOAT,
            final_mass FLOAT,
            energy_released FLOAT,
            FOREIGN KEY (bh1_id) REFERENCES black_holes(bh_id),
            FOREIGN KEY (bh2_id) REFERENCES black_holes(bh_id)
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS saved_dashboards (
            dashboard_id SERIAL PRIMARY KEY,
            dashboard_name VARCHAR(200) NOT NULL,
            report_type VARCHAR(100) NOT NULL,
            bh_id INT,
            observatory_id INT,
            obs_type_id INT,
            start_date DATE,
            end_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            description TEXT
        );
    """)
    
    cur.execute("""
        CREATE TABLE audit_log (
            audit_id SERIAL PRIMARY KEY,
            table_name VARCHAR(50),
            operation VARCHAR(10),
            record_id INT,
            old_data TEXT,
            new_data TEXT,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            changed_by VARCHAR(50) DEFAULT 'system'
        );
    """)
    
    observatories = [
        ('Chandra X-ray Observatory', 'Space', 'X-ray', 1999),
        ('Event Horizon Telescope', 'Global', 'Radio', 2015),
        ('LIGO', 'USA', 'Gravitational Wave', 2015),
        ('Virgo', 'Italy', 'Gravitational Wave', 2007),
        ('Hubble Space Telescope', 'Space', 'Optical', 1990),
        ('NuSTAR', 'Space', 'X-ray', 2012)
    ]
    
    for obs in observatories:
        cur.execute("INSERT INTO observatories (name, location, type, operational_since) VALUES (%s, %s, %s, %s)", obs)

    observation_types = [
        ('X-ray', 'High energy electromagnetic radiation', '0.01nm - 10nm'),
        ('Radio', 'Low frequency electromagnetic radiation', '1mm - 1m'),
        ('Optical', 'Visible light spectrum', '400nm - 700nm'),
        ('Infrared', 'Heat radiation', '700nm - 1mm'),
        ('Gravitational Wave', 'Ripples in spacetime', 'N/A')
    ]

    for obs_type in observation_types:
        cur.execute("INSERT INTO observation_types (type_name, description, wavelength_range) VALUES (%s, %s, %s)", obs_type)

    wavelength_ranges = [
        ('X-ray', 0.01, 10.0, 'nm'),
        ('Ultraviolet', 10.0, 400.0, 'nm'),
        ('Visible', 400.0, 700.0, 'nm'),
        ('Infrared', 700.0, 1000000.0, 'nm'),
        ('Microwave', 1000000.0, 1000000000.0, 'nm'),
        ('Radio', 1000000000.0, 1000000000000.0, 'nm')
    ]

    for wl in wavelength_ranges:
        cur.execute("INSERT INTO wavelength_ranges (wavelength_name, min_wavelength, max_wavelength, unit) VALUES (%s, %s, %s, %s)", wl)

    discovery_methods = [
        ('Radio Telescope', 1930, 'Detection via radio frequency signals'),
        ('X-ray Telescope', 1960, 'Detection via X-ray emissions'),
        ('Optical Telescope', 1600, 'Detection via visible light'),
        ('Gravitational Wave Detection', 2015, 'Detection via LIGO/Virgo'),
        ('Infrared Telescope', 1970, 'Detection via infrared radiation')
    ]

    for method in discovery_methods:
        cur.execute("INSERT INTO discovery_methods (method_name, year_developed, description) VALUES (%s, %s, %s)", method)
    
    black_holes = [
        ('Cygnus X-1', 14.8, 6070, 'Stellar', 1964, 1, 299.590, 35.202),
        ('M87*', 6500000, 53000000, 'Supermassive', 2019, 2, 187.706, 12.391),
        ('Sagittarius A*', 4000000, 26000, 'Supermassive', 1974, 1, 266.417, -29.008),
        ('TON 618', 66000000, 18200000, 'Supermassive', 1957, 1, 53.100, 1.537),
        ('ULAS J1342+0928', 800000000, 13100000, 'Supermassive', 2017, 2, 205.600, 9.342),
        ('V404 Cygni', 9, 7800, 'Stellar', 1989, 1, 306.019, 33.534),
        ('GRS 1915+105', 12, 36000, 'Stellar', 1992, 1, 288.798, 11.156),
        ('Mrk 421', 300000000, 400000, 'Supermassive', 1966, 1, 166.114, 38.209)
    ]

    for bh in black_holes:
        cur.execute("INSERT INTO black_holes (name, mass_solar_masses, distance_light_years, classification, discovery_year, discovery_method_id, ra, dec) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", bh)
    
    for bh_id in range(1, 9):
        for _ in range(random.randint(3, 8)):
            obs_date = datetime.now() - timedelta(days=random.randint(1, 365))
            type_id = random.randint(1, 5)
            wavelength_id = random.randint(1, 6)
            observatory_id = random.randint(1, 6)
            intensity = random.uniform(0.1, 100.0)
            cur.execute(
                "INSERT INTO observations (bh_id, observatory_id, observation_date, type_id, wavelength_id, intensity) VALUES (%s, %s, %s, %s, %s, %s)",
                (bh_id, observatory_id, obs_date.date(), type_id, wavelength_id, intensity)
            )
    
    gw_events = [
        ('GW150914', 1, 2, '2015-09-14', 36.0, 29.0, 62.0, 3.0),
        ('GW170814', 3, 4, '2017-08-14', 30.5, 25.3, 53.0, 2.7),
        ('GW190412', 1, 5, '2019-04-12', 29.4, 2.6, 31.3, 1.0)
    ]
    
    for event in gw_events:
        cur.execute(
            "INSERT INTO gravitational_wave_events (event_name, bh1_id, bh2_id, event_date, mass_1, mass_2, final_mass, energy_released) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            event
        )
    
    cur.execute("""
        CREATE OR REPLACE FUNCTION get_most_observed_bh(p_limit INT DEFAULT 5)
        RETURNS TABLE (bh_name VARCHAR, observation_count BIGINT) AS $$
        BEGIN
            RETURN QUERY
            SELECT b.name, COUNT(o.obs_id) as count
            FROM black_holes b
            LEFT JOIN observations o ON b.bh_id = o.bh_id
            GROUP BY b.bh_id, b.name
            ORDER BY count DESC
            LIMIT p_limit;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    cur.execute("""
        CREATE OR REPLACE FUNCTION get_avg_intensity_per_bh()
        RETURNS TABLE (bh_name VARCHAR, avg_intensity NUMERIC) AS $$
        BEGIN
            RETURN QUERY
            SELECT b.name, AVG(o.intensity)::NUMERIC
            FROM black_holes b
            LEFT JOIN observations o ON b.bh_id = o.bh_id
            WHERE o.intensity IS NOT NULL
            GROUP BY b.bh_id, b.name
            ORDER BY avg_intensity DESC;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    cur.execute("""
        CREATE OR REPLACE FUNCTION get_observations_by_type()
        RETURNS TABLE (type_name VARCHAR, observation_count BIGINT) AS $$
        BEGIN
            RETURN QUERY
            SELECT ot.type_name, COUNT(o.obs_id) as count
            FROM observation_types ot
            LEFT JOIN observations o ON ot.type_id = o.type_id
            GROUP BY ot.type_id, ot.type_name
            ORDER BY count DESC;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    cur.execute("""
        CREATE OR REPLACE FUNCTION audit_trigger_func()
        RETURNS TRIGGER AS $$
        BEGIN
            IF (TG_OP = 'DELETE') THEN
                INSERT INTO audit_log (table_name, operation, record_id, old_data)
                VALUES (TG_TABLE_NAME, TG_OP, OLD.bh_id, row_to_json(OLD)::TEXT);
                RETURN OLD;
            ELSIF (TG_OP = 'UPDATE') THEN
                INSERT INTO audit_log (table_name, operation, record_id, old_data, new_data)
                VALUES (TG_TABLE_NAME, TG_OP, NEW.bh_id, row_to_json(OLD)::TEXT, row_to_json(NEW)::TEXT);
                RETURN NEW;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    cur.execute("""
        DROP TRIGGER IF EXISTS black_holes_audit_trigger ON black_holes;
        CREATE TRIGGER black_holes_audit_trigger
        AFTER UPDATE OR DELETE ON black_holes
        FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
    """)
    
    cur.execute("""
        DROP TRIGGER IF EXISTS observations_audit_trigger ON observations;
        CREATE TRIGGER observations_audit_trigger
        AFTER UPDATE OR DELETE ON observations
        FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
    """)
    
    cur.execute("""
        CREATE OR REPLACE FUNCTION cleanup_old_audit_logs()
        RETURNS void AS $$
        BEGIN
            DELETE FROM audit_log 
            WHERE changed_at < NOW() - INTERVAL '90 days';
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    cur.execute("CREATE INDEX IF NOT EXISTS idx_observations_bh_id ON observations(bh_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_observations_observatory_id ON observations(observatory_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_observations_date ON observations(observation_date);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_observations_type_id ON observations(type_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_black_holes_classification ON black_holes(classification);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_black_holes_name ON black_holes(name);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_date ON audit_log(changed_at);")
    
    conn.commit()
    cur.close()
    conn.close()
    print("Database initialized successfully!")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/view_data')
def view_data():
    """Menu page for viewing all different data types"""
    return render_template('view_data.html')


# DISCOVERY METHODS CRUD

@app.route('/discovery_methods')
def view_discovery_methods():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT method_id, method_name, year_developed, description FROM discovery_methods ORDER BY year_developed DESC;")
    methods = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('discovery_methods.html', methods=methods)

@app.route('/add_discovery_method', methods=['GET', 'POST'])
def add_discovery_method():
    if request.method == 'POST':
        try:
            method_name = request.form.get('method_name', '').strip()
            year_developed = request.form.get('year_developed', '')
            description = request.form.get('description', '').strip()
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO discovery_methods (method_name, year_developed, description) VALUES (%s, %s, %s)",
                       (method_name, int(year_developed), description))
            conn.commit()
            cur.close()
            conn.close()
            flash('✅ Discovery method added successfully!', 'success')
            return redirect(url_for('view_discovery_methods'))
        except Exception as e:
            print(f"Error: {str(e)}")
            flash(f'❌ Error adding discovery method: {str(e)}', 'danger')
            return render_template('add_discovery_method.html', error=str(e))
    return render_template('add_discovery_method.html')

@app.route('/edit_discovery_method/<int:method_id>', methods=['GET', 'POST'])
def edit_discovery_method(method_id):
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        try:
            method_name = request.form.get('method_name', '').strip()
            year_developed = request.form.get('year_developed', '')
            description = request.form.get('description', '').strip()
            cur.execute("UPDATE discovery_methods SET method_name = %s, year_developed = %s, description = %s WHERE method_id = %s",
                       (method_name, int(year_developed), description, method_id))
            conn.commit()
            cur.close()
            conn.close()
            flash('✅ Discovery method updated successfully!', 'success')
            return redirect(url_for('view_discovery_methods'))
        except Exception as e:
            print(f"Error updating discovery method: {str(e)}")
            flash(f'❌ Error updating discovery method: {str(e)}', 'danger')
            cur.execute("SELECT method_id, method_name, year_developed, description FROM discovery_methods WHERE method_id = %s", (method_id,))
            method = cur.fetchone()
            cur.close()
            conn.close()
            return render_template('edit_discovery_method.html', method=method, error=str(e))
    cur.execute("SELECT method_id, method_name, year_developed, description FROM discovery_methods WHERE method_id = %s", (method_id,))
    method = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('edit_discovery_method.html', method=method)

@app.route('/delete_discovery_method/<int:method_id>', methods=['POST'])
def delete_discovery_method(method_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM discovery_methods WHERE method_id = %s", (method_id,))
        conn.commit()
        cur.close()
        conn.close()
        flash('✅ Discovery method deleted successfully!', 'success')
    except Exception as e:
        flash(f'❌ Error deleting discovery method: {str(e)}', 'danger')
        print(f"Error deleting discovery method: {str(e)}")
    return redirect(url_for('view_discovery_methods'))


# WAVELENGTH RANGES CRUD

@app.route('/wavelength_ranges')
def view_wavelength_ranges():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT wavelength_id, wavelength_name, min_wavelength, max_wavelength, unit FROM wavelength_ranges ORDER BY min_wavelength;")
    wavelengths = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('wavelength_ranges.html', wavelengths=wavelengths)

@app.route('/add_wavelength_range', methods=['GET', 'POST'])
def add_wavelength_range():
    if request.method == 'POST':
        try:
            wavelength_name = request.form.get('wavelength_name', '').strip()
            min_wavelength = float(request.form.get('min_wavelength', 0))
            max_wavelength = float(request.form.get('max_wavelength', 0))
            unit = request.form.get('unit', '').strip()
            
            errors = []
            if not wavelength_name:
                errors.append("Wavelength name is required")
            if min_wavelength <= 0:
                errors.append("Minimum wavelength must be positive")
            if max_wavelength <= 0:
                errors.append("Maximum wavelength must be positive")
            if min_wavelength >= max_wavelength:
                errors.append("Minimum wavelength must be less than maximum wavelength")
            if not unit:
                errors.append("Unit is required")
            
            if errors:
                flash(f'❌ {"; ".join(errors)}', 'danger')
                return render_template('add_wavelength_range.html', error="; ".join(errors))
            
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO wavelength_ranges (wavelength_name, min_wavelength, max_wavelength, unit) VALUES (%s, %s, %s, %s)",
                       (wavelength_name, min_wavelength, max_wavelength, unit))
            conn.commit()
            cur.close()
            conn.close()
            flash('✅ Wavelength range added successfully!', 'success')
            return redirect(url_for('view_wavelength_ranges'))
        except Exception as e:
            flash(f'❌ Error adding wavelength range: {str(e)}', 'danger')
            return render_template('add_wavelength_range.html', error=str(e))
    return render_template('add_wavelength_range.html')

@app.route('/edit_wavelength_range/<int:wavelength_id>', methods=['GET', 'POST'])
def edit_wavelength_range(wavelength_id):
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        try:
            wavelength_name = request.form.get('wavelength_name', '').strip()
            min_wavelength = float(request.form.get('min_wavelength', 0))
            max_wavelength = float(request.form.get('max_wavelength', 0))
            unit = request.form.get('unit', '').strip()
            cur.execute("UPDATE wavelength_ranges SET wavelength_name = %s, min_wavelength = %s, max_wavelength = %s, unit = %s WHERE wavelength_id = %s",
                       (wavelength_name, min_wavelength, max_wavelength, unit, wavelength_id))
            conn.commit()
            cur.close()
            conn.close()
            flash('✅ Wavelength range updated successfully!', 'success')
            return redirect(url_for('view_wavelength_ranges'))
        except Exception as e:
            print(f"Error updating wavelength range: {str(e)}")
            flash(f'❌ Error updating wavelength range: {str(e)}', 'danger')
            cur.execute("SELECT wavelength_id, wavelength_name, min_wavelength, max_wavelength, unit FROM wavelength_ranges WHERE wavelength_id = %s", (wavelength_id,))
            wavelength = cur.fetchone()
            cur.close()
            conn.close()
            return render_template('edit_wavelength_range.html', wavelength=wavelength, error=str(e))
    cur.execute("SELECT wavelength_id, wavelength_name, min_wavelength, max_wavelength, unit FROM wavelength_ranges WHERE wavelength_id = %s", (wavelength_id,))
    wavelength = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('edit_wavelength_range.html', wavelength=wavelength)

@app.route('/delete_wavelength_range/<int:wavelength_id>', methods=['POST'])
def delete_wavelength_range(wavelength_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM wavelength_ranges WHERE wavelength_id = %s", (wavelength_id,))
        conn.commit()
        cur.close()
        conn.close()
        flash('✅ Wavelength range deleted successfully!', 'success')
    except Exception as e:
        flash(f'❌ Error deleting wavelength range: {str(e)}', 'danger')
        print(f"Error deleting wavelength range: {str(e)}")
    return redirect(url_for('view_wavelength_ranges'))


# OBSERVATION TYPES CRUD

@app.route('/observation_types')
def view_observation_types():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT type_id, type_name, description, wavelength_range FROM observation_types ORDER BY type_name;")
    types = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('observation_types.html', types=types)

@app.route('/add_observation_type', methods=['GET', 'POST'])
def add_observation_type():
    if request.method == 'POST':
        try:
            type_name = request.form.get('type_name', '').strip()
            description = request.form.get('description', '').strip()
            wavelength_range = request.form.get('wavelength_range', '').strip()
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO observation_types (type_name, description, wavelength_range) VALUES (%s, %s, %s)",
                       (type_name, description, wavelength_range))
            conn.commit()
            cur.close()
            conn.close()
            flash('✅ Observation type added successfully!', 'success')
            return redirect(url_for('view_observation_types'))
        except Exception as e:
            flash(f'❌ Error adding observation type: {str(e)}', 'danger')
            return render_template('add_observation_type.html', error=str(e))
    return render_template('add_observation_type.html')

@app.route('/edit_observation_type/<int:type_id>', methods=['GET', 'POST'])
def edit_observation_type(type_id):
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        try:
            type_name = request.form.get('type_name', '').strip()
            description = request.form.get('description', '').strip()
            wavelength_range = request.form.get('wavelength_range', '').strip()
            cur.execute("UPDATE observation_types SET type_name = %s, description = %s, wavelength_range = %s WHERE type_id = %s",
                       (type_name, description, wavelength_range, type_id))
            conn.commit()
            cur.close()
            conn.close()
            flash('✅ Observation type updated successfully!', 'success')
            return redirect(url_for('view_observation_types'))
        except Exception as e:
            print(f"Error updating observation type: {str(e)}")
            flash(f'❌ Error updating observation type: {str(e)}', 'danger')
            cur.execute("SELECT type_id, type_name, description, wavelength_range FROM observation_types WHERE type_id = %s", (type_id,))
            obs_type = cur.fetchone()
            cur.close()
            conn.close()
            return render_template('edit_observation_type.html', obs_type=obs_type, error=str(e))
    cur.execute("SELECT type_id, type_name, description, wavelength_range FROM observation_types WHERE type_id = %s", (type_id,))
    obs_type = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('edit_observation_type.html', obs_type=obs_type)

@app.route('/delete_observation_type/<int:type_id>', methods=['POST'])
def delete_observation_type(type_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM observation_types WHERE type_id = %s", (type_id,))
        conn.commit()
        cur.close()
        conn.close()
        flash('✅ Observation type deleted successfully!', 'success')
    except Exception as e:
        flash(f'❌ Error deleting observation type: {str(e)}', 'danger')
        print(f"Error deleting observation type: {str(e)}")
    return redirect(url_for('view_observation_types'))


# OBSERVATORIES CRUD

@app.route('/observatories')
def view_observatories():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT observatory_id, name, location, type, operational_since FROM observatories ORDER BY name;")
    observatories = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('observatories.html', observatories=observatories)

@app.route('/add_observatory', methods=['GET', 'POST'])
def add_observatory():
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            location = request.form.get('location', '').strip()
            obs_type = request.form.get('type', '').strip()
            operational_since = request.form.get('operational_since', '')
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO observatories (name, location, type, operational_since) VALUES (%s, %s, %s, %s)",
                       (name, location, obs_type, int(operational_since)))
            conn.commit()
            cur.close()
            conn.close()
            flash('✅ Observatory added successfully!', 'success')
            return redirect(url_for('view_observatories'))
        except Exception as e:
            flash(f'❌ Error adding observatory: {str(e)}', 'danger')
            return render_template('add_observatory.html', error=str(e))
    return render_template('add_observatory.html')

@app.route('/edit_observatory/<int:observatory_id>', methods=['GET', 'POST'])
def edit_observatory(observatory_id):
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            location = request.form.get('location', '').strip()
            obs_type = request.form.get('type', '').strip()
            operational_since = request.form.get('operational_since', '')
            cur.execute("UPDATE observatories SET name = %s, location = %s, type = %s, operational_since = %s WHERE observatory_id = %s",
                       (name, location, obs_type, int(operational_since), observatory_id))
            conn.commit()
            cur.close()
            conn.close()
            flash('✅ Observatory updated successfully!', 'success')
            return redirect(url_for('view_observatories'))
        except Exception as e:
            print(f"Error updating observatory: {str(e)}")
            flash(f'❌ Error updating observatory: {str(e)}', 'danger')
            cur.execute("SELECT observatory_id, name, location, type, operational_since FROM observatories WHERE observatory_id = %s", (observatory_id,))
            observatory = cur.fetchone()
            cur.close()
            conn.close()
            return render_template('edit_observatory.html', observatory=observatory, error=str(e))
    cur.execute("SELECT observatory_id, name, location, type, operational_since FROM observatories WHERE observatory_id = %s", (observatory_id,))
    observatory = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('edit_observatory.html', observatory=observatory)

@app.route('/delete_observatory/<int:observatory_id>', methods=['POST'])
def delete_observatory(observatory_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM observatories WHERE observatory_id = %s", (observatory_id,))
        conn.commit()
        cur.close()
        conn.close()
        flash('✅ Observatory deleted successfully!', 'success')
    except Exception as e:
        flash(f'❌ Error deleting observatory: {str(e)}', 'danger')
        print(f"Error deleting observatory: {str(e)}")
    return redirect(url_for('view_observatories'))


# BLACK HOLES CRUD
@app.route('/black_holes')
def view_black_holes():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT b.bh_id, b.name, b.mass_solar_masses, b.distance_light_years, 
               b.classification, b.discovery_year, d.method_name
        FROM black_holes b
        LEFT JOIN discovery_methods d ON b.discovery_method_id = d.method_id
        ORDER BY b.name;
    """)
    black_holes = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('black_holes.html', black_holes=black_holes)

@app.route('/add_black_hole', methods=['GET', 'POST'])
def add_black_hole():
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            mass = float(request.form.get('mass_solar_masses', 0))
            distance = float(request.form.get('distance_light_years', 0))
            classification = request.form.get('classification', '').strip()
            discovery_year = int(request.form.get('discovery_year', 0))
            discovery_method_id = request.form.get('discovery_method_id', '')
            ra = float(request.form.get('ra', 0))
            dec = float(request.form.get('dec', 0))
            
            current_year = datetime.now().year
            errors = []
            if not name:
                errors.append("Name is required")
            if mass <= 0:
                errors.append("Mass must be positive")
            if distance <= 0:
                errors.append("Distance must be positive")
            if not classification:
                errors.append("Classification is required")
            if discovery_year > current_year:
                errors.append(f"Discovery year cannot be in the future (current year: {current_year})")
            if discovery_year < 1600:
                errors.append("Discovery year must be 1600 or later")
            if ra < 0 or ra > 360:
                errors.append("Right Ascension must be between 0 and 360")
            if dec < -90 or dec > 90:
                errors.append("Declination must be between -90 and 90")
            
            if errors:
                flash(f'❌ {"; ".join(errors)}', 'danger')
                cur.execute("SELECT method_id, method_name FROM discovery_methods ORDER BY method_name;")
                methods = cur.fetchall()
                cur.close()
                conn.close()
                return render_template('add_black_hole.html', error="; ".join(errors), methods=methods)
            
            cur.execute("INSERT INTO black_holes (name, mass_solar_masses, distance_light_years, classification, discovery_year, discovery_method_id, ra, dec) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                       (name, mass, distance, classification, discovery_year, discovery_method_id if discovery_method_id else None, ra, dec))
            conn.commit()
            cur.close()
            conn.close()
            flash('✅ Black hole added successfully!', 'success')
            return redirect(url_for('view_black_holes'))
        except Exception as e:
            print(f"Error: {str(e)}")
            flash(f'❌ Error adding black hole: {str(e)}', 'danger')
            cur.execute("SELECT method_id, method_name FROM discovery_methods ORDER BY method_name;")
            methods = cur.fetchall()
            cur.close()
            conn.close()
            return render_template('add_black_hole.html', error=str(e), methods=methods)
    cur.execute("SELECT method_id, method_name FROM discovery_methods ORDER BY method_name;")
    methods = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('add_black_hole.html', methods=methods)

@app.route('/edit_black_hole/<int:bh_id>', methods=['GET', 'POST'])
def edit_black_hole(bh_id):
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            mass = float(request.form.get('mass_solar_masses', 0))
            distance = float(request.form.get('distance_light_years', 0))
            classification = request.form.get('classification', '').strip()
            discovery_year = int(request.form.get('discovery_year', 0))
            discovery_method_id = request.form.get('discovery_method_id', '')
            ra = float(request.form.get('ra', 0))
            dec = float(request.form.get('dec', 0))
            cur.execute("UPDATE black_holes SET name = %s, mass_solar_masses = %s, distance_light_years = %s, classification = %s, discovery_year = %s, discovery_method_id = %s, ra = %s, dec = %s WHERE bh_id = %s",
                       (name, mass, distance, classification, discovery_year, discovery_method_id if discovery_method_id else None, ra, dec, bh_id))
            conn.commit()
            cur.close()
            conn.close()
            flash('✅ Black hole updated successfully!', 'success')
            return redirect(url_for('view_black_holes'))
        except Exception as e:
            print(f"Error updating black hole: {str(e)}")
            flash(f'❌ Error updating black hole: {str(e)}', 'danger')
            cur.execute("SELECT bh_id, name, mass_solar_masses, distance_light_years, classification, discovery_year, discovery_method_id, ra, dec FROM black_holes WHERE bh_id = %s", (bh_id,))
            black_hole = cur.fetchone()
            cur.execute("SELECT method_id, method_name FROM discovery_methods ORDER BY method_name;")
            methods = cur.fetchall()
            cur.close()
            conn.close()
            return render_template('edit_black_hole.html', black_hole=black_hole, methods=methods, error=str(e))
    cur.execute("SELECT bh_id, name, mass_solar_masses, distance_light_years, classification, discovery_year, discovery_method_id, ra, dec FROM black_holes WHERE bh_id = %s", (bh_id,))
    black_hole = cur.fetchone()
    cur.execute("SELECT method_id, method_name FROM discovery_methods ORDER BY method_name;")
    methods = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('edit_black_hole.html', black_hole=black_hole, methods=methods)

@app.route('/delete_black_hole/<int:bh_id>', methods=['POST'])
def delete_black_hole(bh_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM black_holes WHERE bh_id = %s", (bh_id,))
        conn.commit()
        cur.close()
        conn.close()
        flash('✅ Black hole deleted successfully!', 'success')
    except Exception as e:
        flash(f'❌ Error deleting black hole: {str(e)}', 'danger')
        print(f"Error deleting black hole: {str(e)}")
    return redirect(url_for('view_black_holes'))


# GRAVITATIONAL WAVE EVENTS CRUD

@app.route('/gw_events')
def view_gw_events():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT gw.gw_event_id, gw.event_name, b1.name, b2.name, gw.event_date, 
               gw.mass_1, gw.mass_2, gw.final_mass, gw.energy_released
        FROM gravitational_wave_events gw
        JOIN black_holes b1 ON gw.bh1_id = b1.bh_id
        JOIN black_holes b2 ON gw.bh2_id = b2.bh_id
        ORDER BY gw.event_date DESC;
    """)
    events = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('gw_events.html', events=events)

@app.route('/add_gw_event', methods=['GET', 'POST'])
def add_gw_event():
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        try:
            event_name = request.form.get('event_name', '').strip()
            bh1_id = request.form.get('bh1_id')
            bh2_id = request.form.get('bh2_id')
            event_date = request.form.get('event_date')
            mass_1 = float(request.form.get('mass_1', 0))
            mass_2 = float(request.form.get('mass_2', 0))
            final_mass = float(request.form.get('final_mass', 0))
            energy_released = float(request.form.get('energy_released', 0))
            cur.execute("INSERT INTO gravitational_wave_events (event_name, bh1_id, bh2_id, event_date, mass_1, mass_2, final_mass, energy_released) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                       (event_name, bh1_id, bh2_id, event_date, mass_1, mass_2, final_mass, energy_released))
            conn.commit()
            cur.close()
            conn.close()
            flash('✅ Gravitational wave event added successfully!', 'success')
            return redirect(url_for('view_gw_events'))
        except Exception as e:
            flash(f'❌ Error adding GW event: {str(e)}', 'danger')
            cur.execute("SELECT bh_id, name FROM black_holes ORDER BY name;")
            black_holes = cur.fetchall()
            cur.close()
            conn.close()
            return render_template('add_gw_event.html', error=str(e), black_holes=black_holes)
    cur.execute("SELECT bh_id, name FROM black_holes ORDER BY name;")
    black_holes = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('add_gw_event.html', black_holes=black_holes)

@app.route('/edit_gw_event/<int:gw_event_id>', methods=['GET', 'POST'])
def edit_gw_event(gw_event_id):
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        try:
            event_name = request.form.get('event_name', '').strip()
            event_date = request.form.get('event_date')
            mass_1 = float(request.form.get('mass_1', 0))
            mass_2 = float(request.form.get('mass_2', 0))
            final_mass = float(request.form.get('final_mass', 0))
            energy_released = float(request.form.get('energy_released', 0))
            cur.execute("UPDATE gravitational_wave_events SET event_name = %s, event_date = %s, mass_1 = %s, mass_2 = %s, final_mass = %s, energy_released = %s WHERE gw_event_id = %s",
                       (event_name, event_date, mass_1, mass_2, final_mass, energy_released, gw_event_id))
            conn.commit()
            cur.close()
            conn.close()
            flash('✅ Gravitational wave event updated successfully!', 'success')
            return redirect(url_for('view_gw_events'))
        except Exception as e:
            print(f"Error updating gravitational wave event: {str(e)}")
            flash(f'❌ Error updating GW event: {str(e)}', 'danger')
            cur.execute("SELECT gw_event_id, event_name, bh1_id, bh2_id, event_date, mass_1, mass_2, final_mass, energy_released FROM gravitational_wave_events WHERE gw_event_id = %s", (gw_event_id,))
            event = cur.fetchone()
            cur.close()
            conn.close()
            return render_template('edit_gw_event.html', event=event, error=str(e))
    cur.execute("SELECT gw_event_id, event_name, bh1_id, bh2_id, event_date, mass_1, mass_2, final_mass, energy_released FROM gravitational_wave_events WHERE gw_event_id = %s", (gw_event_id,))
    event = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('edit_gw_event.html', event=event)

@app.route('/delete_gw_event/<int:gw_event_id>', methods=['POST'])
def delete_gw_event(gw_event_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM gravitational_wave_events WHERE gw_event_id = %s", (gw_event_id,))
        conn.commit()
        cur.close()
        conn.close()
        flash('✅ Gravitational wave event deleted successfully!', 'success')
    except Exception as e:
        flash(f'❌ Error deleting GW event: {str(e)}', 'danger')
        print(f"Error deleting gravitational wave event: {str(e)}")
    return redirect(url_for('view_gw_events'))


# OBSERVATIONS CRUD

@app.route('/observations')
def view_observations():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT o.obs_id, b.name, obs.name, o.observation_date, ot.type_name, o.intensity
        FROM observations o
        JOIN black_holes b ON o.bh_id = b.bh_id
        JOIN observatories obs ON o.observatory_id = obs.observatory_id
        LEFT JOIN observation_types ot ON o.type_id = ot.type_id
        ORDER BY o.observation_date DESC;
    """)
    observations = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('observations.html', observations=observations)

@app.route('/add_observation', methods=['GET', 'POST'])
def add_observation():
    conn = get_db_connection()
    cur = conn.cursor()
    
    if request.method == 'POST':
        try:
            bh_id = request.form['bh_id']
            observatory_id = request.form['observatory_id']
            obs_date = request.form['obs_date']
            type_id = request.form['type_id']
            wavelength_id = request.form.get('wavelength_id', None)
            intensity = request.form.get('intensity', 0)
            notes = request.form.get('notes', '').strip()
            
            errors = []
            if not bh_id:
                errors.append("Black hole is required")
            if not observatory_id:
                errors.append("Observatory is required")
            if not obs_date:
                errors.append("Observation date is required")
            if not type_id:
                errors.append("Observation type is required")
            if intensity and float(intensity) < 0:
                errors.append("Intensity cannot be negative")
            
            obs_date_obj = datetime.strptime(obs_date, '%Y-%m-%d')
            if obs_date_obj > datetime.now():
                errors.append("Observation date cannot be in the future")
            
            if errors:
                flash(f'❌ {"; ".join(errors)}', 'danger')
                cur.execute("SELECT bh_id, name FROM black_holes ORDER BY name;")
                black_holes = cur.fetchall()
                cur.execute("SELECT observatory_id, name FROM observatories ORDER BY name;")
                observatories = cur.fetchall()
                cur.execute("SELECT type_id, type_name FROM observation_types ORDER BY type_name;")
                obs_types = cur.fetchall()
                cur.execute("SELECT wavelength_id, wavelength_name FROM wavelength_ranges ORDER BY wavelength_name;")
                wavelengths = cur.fetchall()
                cur.close()
                conn.close()
                return render_template('add_observation.html', black_holes=black_holes, observatories=observatories, obs_types=obs_types, wavelengths=wavelengths, error="; ".join(errors))
            
            cur.execute(
                "INSERT INTO observations (bh_id, observatory_id, observation_date, type_id, wavelength_id, intensity, notes) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (bh_id, observatory_id, obs_date, type_id, wavelength_id, intensity, notes)
            )
            conn.commit()
            cur.close()
            conn.close()
            flash('✅ Observation added successfully!', 'success')
            return redirect(url_for('view_observations'))
        except Exception as e:
            print(f"Error adding observation: {str(e)}")
            flash(f'❌ Error adding observation: {str(e)}', 'danger')
            cur.execute("SELECT bh_id, name FROM black_holes ORDER BY name;")
            black_holes = cur.fetchall()
            cur.execute("SELECT observatory_id, name FROM observatories ORDER BY name;")
            observatories = cur.fetchall()
            cur.execute("SELECT type_id, type_name FROM observation_types ORDER BY type_name;")
            obs_types = cur.fetchall()
            cur.execute("SELECT wavelength_id, wavelength_name FROM wavelength_ranges ORDER BY wavelength_name;")
            wavelengths = cur.fetchall()
            cur.close()
            conn.close()
            return render_template('add_observation.html', black_holes=black_holes, observatories=observatories, obs_types=obs_types, wavelengths=wavelengths, error=str(e))
    
    cur.execute("SELECT bh_id, name FROM black_holes ORDER BY name;")
    black_holes = cur.fetchall()
    cur.execute("SELECT observatory_id, name FROM observatories ORDER BY name;")
    observatories = cur.fetchall()
    cur.execute("SELECT type_id, type_name FROM observation_types ORDER BY type_name;")
    obs_types = cur.fetchall()
    cur.execute("SELECT wavelength_id, wavelength_name FROM wavelength_ranges ORDER BY wavelength_name;")
    wavelengths = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('add_observation.html', black_holes=black_holes, observatories=observatories, obs_types=obs_types, wavelengths=wavelengths)

@app.route('/edit_observation/<int:obs_id>', methods=['GET', 'POST'])
def edit_observation(obs_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    if request.method == 'POST':
        try:
            bh_id = request.form['bh_id']
            observatory_id = request.form['observatory_id']
            obs_date = request.form['obs_date']
            type_id = request.form['type_id']
            wavelength_id = request.form.get('wavelength_id', None)
            intensity = request.form.get('intensity', 0)
            notes = request.form.get('notes', '').strip()
            
            cur.execute("""
                UPDATE observations 
                SET bh_id = %s, observatory_id = %s, observation_date = %s, 
                    type_id = %s, wavelength_id = %s, intensity = %s, notes = %s 
                WHERE obs_id = %s
            """, (bh_id, observatory_id, obs_date, type_id, wavelength_id, intensity, notes, obs_id))
            
            conn.commit()
            cur.close()
            conn.close()
            flash('✅ Observation updated successfully!', 'success')
            return redirect(url_for('view_observations'))
        except Exception as e:
            print(f"Error updating observation: {str(e)}")
            flash(f'❌ Error updating observation: {str(e)}', 'danger')
            cur.execute("""
                SELECT obs_id, bh_id, observatory_id, observation_date, 
                       type_id, wavelength_id, intensity, notes
                FROM observations WHERE obs_id = %s
            """, (obs_id,))
            observation = cur.fetchone()
            cur.execute("SELECT bh_id, name FROM black_holes ORDER BY name;")
            black_holes = cur.fetchall()
            cur.execute("SELECT observatory_id, name FROM observatories ORDER BY name;")
            observatories = cur.fetchall()
            cur.execute("SELECT type_id, type_name FROM observation_types ORDER BY type_name;")
            obs_types = cur.fetchall()
            cur.execute("SELECT wavelength_id, wavelength_name FROM wavelength_ranges ORDER BY wavelength_name;")
            wavelengths = cur.fetchall()
            cur.close()
            conn.close()
            return render_template('edit_observation.html', observation=observation, black_holes=black_holes, observatories=observatories, obs_types=obs_types, wavelengths=wavelengths, error=str(e))
    
    cur.execute("""
        SELECT obs_id, bh_id, observatory_id, observation_date, 
               type_id, wavelength_id, intensity, notes
        FROM observations WHERE obs_id = %s
    """, (obs_id,))
    observation = cur.fetchone()
    
    cur.execute("SELECT bh_id, name FROM black_holes ORDER BY name;")
    black_holes = cur.fetchall()
    cur.execute("SELECT observatory_id, name FROM observatories ORDER BY name;")
    observatories = cur.fetchall()
    cur.execute("SELECT type_id, type_name FROM observation_types ORDER BY type_name;")
    obs_types = cur.fetchall()
    cur.execute("SELECT wavelength_id, wavelength_name FROM wavelength_ranges ORDER BY wavelength_name;")
    wavelengths = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('edit_observation.html', observation=observation, black_holes=black_holes, observatories=observatories, obs_types=obs_types, wavelengths=wavelengths)

@app.route('/delete_observation/<int:obs_id>', methods=['POST'])
def delete_observation(obs_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM observations WHERE obs_id = %s", (obs_id,))
        conn.commit()
        cur.close()
        conn.close()
        flash('✅ Observation deleted successfully!', 'success')
    except Exception as e:
        flash(f'❌ Error deleting observation: {str(e)}', 'danger')
        print(f"Error deleting observation: {str(e)}")
    return redirect(url_for('view_observations'))


# OTHER ROUTES


@app.route('/search', methods=['GET', 'POST'])
def search():
    results = []
    error = None
    if request.method == 'POST':
        try:
            name = request.form.get('name', '')
            mass_min = request.form.get('mass_min', 0)
            mass_max = request.form.get('mass_max', 999999999999)
            distance_min = request.form.get('distance_min', 0)
            distance_max = request.form.get('distance_max', 999999999999)
            classification = request.form.get('classification', '')
            
            if mass_min and mass_max and float(mass_min) > float(mass_max):
                error = "Minimum mass cannot be greater than maximum mass"
                flash(f'❌ {error}', 'danger')
                return render_template('search.html', results=results, error=error)
            
            if distance_min and distance_max and float(distance_min) > float(distance_max):
                error = "Minimum distance cannot be greater than maximum distance"
                flash(f'❌ {error}', 'danger')
                return render_template('search.html', results=results, error=error)
            
            conn = get_db_connection()
            cur = conn.cursor()
            
            query = "SELECT bh_id, name, mass_solar_masses, distance_light_years, classification, discovery_year FROM black_holes WHERE 1=1"
            params = []
            
            if name:
                query += " AND name ILIKE %s"
                params.append(f"%{name}%")
            if mass_min:
                query += " AND mass_solar_masses >= %s"
                params.append(float(mass_min))
            if mass_max:
                query += " AND mass_solar_masses <= %s"
                params.append(float(mass_max))
            if distance_min:
                query += " AND distance_light_years >= %s"
                params.append(float(distance_min))
            if distance_max:
                query += " AND distance_light_years <= %s"
                params.append(float(distance_max))
            if classification:
                query += " AND classification = %s"
                params.append(classification)
            
            cur.execute(query, params)
            results = cur.fetchall()
            cur.close()
            conn.close()
        except Exception as e:
            error = f"Search error: {str(e)}"
            flash(f'❌ {error}', 'danger')
            print(f"Error in search: {str(e)}")
    
    return render_template('search.html', results=results, error=error)

@app.route('/update/<int:bh_id>', methods=['GET', 'POST'])
def update(bh_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    if request.method == 'POST':
        try:
            mass = request.form.get('mass_solar_masses')
            distance = request.form.get('distance_light_years')
            cur.execute("UPDATE black_holes SET mass_solar_masses = %s, distance_light_years = %s WHERE bh_id = %s",
                        (float(mass), float(distance), bh_id))
            conn.commit()
            cur.close()
            conn.close()
            flash('✅ Black hole data updated successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            print(f"Error updating black hole: {str(e)}")
            flash(f'❌ Error updating black hole: {str(e)}', 'danger')
            cur.execute("SELECT * FROM black_holes WHERE bh_id = %s", (bh_id,))
            black_hole = cur.fetchone()
            cur.close()
            conn.close()
            return render_template('update.html', black_hole=black_hole, error=str(e))
    
    cur.execute("SELECT * FROM black_holes WHERE bh_id = %s", (bh_id,))
    black_hole = cur.fetchone()
    cur.close()
    conn.close()
    
    return render_template('update.html', black_hole=black_hole)

@app.route('/reports')
def reports():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM get_most_observed_bh(10)")
        report1 = cur.fetchall()
        
        cur.execute("""
            SELECT obs.name, COUNT(o.obs_id) as count
            FROM observatories obs
            LEFT JOIN observations o ON obs.observatory_id = o.observatory_id
            GROUP BY obs.observatory_id, obs.name
            ORDER BY count DESC;
        """)
        report2 = cur.fetchall()
        
        cur.execute("""
            SELECT classification, COUNT(*) as count, AVG(mass_solar_masses) as avg_mass
            FROM black_holes
            GROUP BY classification;
        """)
        report3 = cur.fetchall()
        
        cur.execute("""
            SELECT event_name, mass_1, mass_2, final_mass, energy_released, event_date
            FROM gravitational_wave_events
            ORDER BY event_date DESC;
        """)
        report4 = cur.fetchall()
        
        cur.execute("SELECT * FROM get_observations_by_type()")
        report5 = cur.fetchall()
        
        cur.execute("SELECT * FROM get_avg_intensity_per_bh()")
        report6 = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return render_template('reports.html', 
                              report1=report1, report2=report2, report3=report3,
                              report4=report4, report5=report5, report6=report6)
    except Exception as e:
        print(f"Error generating reports: {str(e)}")
        flash(f'❌ Error generating reports: {str(e)}', 'danger')
        return render_template('reports.html', 
                              report1=[], report2=[], report3=[],
                              report4=[], report5=[], report6=[],
                              error=str(e))
 
@app.route('/custom_dashboard', methods=['GET', 'POST'])
def custom_dashboard():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT bh_id, name FROM black_holes ORDER BY name;")
    black_holes = cur.fetchall()
    
    cur.execute("SELECT observatory_id, name FROM observatories ORDER BY name;")
    observatories = cur.fetchall()
    
    cur.execute("SELECT type_id, type_name FROM observation_types ORDER BY type_name;")
    obs_types = cur.fetchall()
    
    results = None
    dashboard_data = None
    
    if request.method == 'POST':
        report_type = request.form.get('report_type')
        bh_id = request.form.get('bh_id')
        observatory_id = request.form.get('observatory_id')
        obs_type_id = request.form.get('obs_type_id')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        action = request.form.get('action')
        
        if action == 'save':
            dashboard_name = request.form.get('dashboard_name')
            description = request.form.get('description')
            
            if dashboard_name and report_type:
                try:
                    cur.execute("""
                        INSERT INTO saved_dashboards 
                        (dashboard_name, report_type, bh_id, observatory_id, obs_type_id, start_date, end_date, description)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (dashboard_name, report_type, bh_id or None, observatory_id or None, obs_type_id or None, start_date or None, end_date or None, description))
                    conn.commit()
                    flash('✅ Dashboard saved successfully!', 'success')
                except Exception as e:
                    flash(f'❌ Error saving dashboard: {str(e)}', 'danger')
                    print(f"Error saving dashboard: {str(e)}")
        
        if report_type == 'observations_by_bh':
            query = """
                SELECT b.name as black_hole, COUNT(*) as count, AVG(o.intensity) as avg_intensity
                FROM observations o
                JOIN black_holes b ON o.bh_id = b.bh_id
                WHERE 1=1
            """
            params = []
            
            if bh_id:
                query += " AND o.bh_id = %s"
                params.append(bh_id)
            if start_date:
                query += " AND o.observation_date >= %s"
                params.append(start_date)
            if end_date:
                query += " AND o.observation_date <= %s"
                params.append(end_date)
                
            query += " GROUP BY b.bh_id, b.name ORDER BY count DESC;"
            
            cur.execute(query, params)
            results = cur.fetchall()
            dashboard_data = {
                'title': 'Observations by Black Hole',
                'columns': ['Black Hole', 'Observation Count', 'Avg Intensity'],
                'results': results
            }
        
        elif report_type == 'observations_by_observatory':
            query = """
                SELECT obs.name as observatory, COUNT(*) as count, AVG(o.intensity) as avg_intensity
                FROM observations o
                JOIN observatories obs ON o.observatory_id = obs.observatory_id
                WHERE 1=1
            """
            params = []
            
            if observatory_id:
                query += " AND o.observatory_id = %s"
                params.append(observatory_id)
            if start_date:
                query += " AND o.observation_date >= %s"
                params.append(start_date)
            if end_date:
                query += " AND o.observation_date <= %s"
                params.append(end_date)
                
            query += " GROUP BY obs.observatory_id, obs.name ORDER BY count DESC;"
            
            cur.execute(query, params)
            results = cur.fetchall()
            dashboard_data = {
                'title': 'Observations by Observatory',
                'columns': ['Observatory', 'Observation Count', 'Avg Intensity'],
                'results': results
            }
        
        elif report_type == 'observations_by_type':
            query = """
                SELECT ot.type_name, COUNT(*) as count, AVG(o.intensity) as avg_intensity
                FROM observations o
                LEFT JOIN observation_types ot ON o.type_id = ot.type_id
                WHERE 1=1
            """
            params = []
            
            if obs_type_id:
                query += " AND o.type_id = %s"
                params.append(obs_type_id)
            if start_date:
                query += " AND o.observation_date >= %s"
                params.append(start_date)
            if end_date:
                query += " AND o.observation_date <= %s"
                params.append(end_date)
                
            query += " GROUP BY ot.type_id, ot.type_name ORDER BY count DESC;"
            
            cur.execute(query, params)
            results = cur.fetchall()
            dashboard_data = {
                'title': 'Observations by Type',
                'columns': ['Observation Type', 'Count', 'Avg Intensity'],
                'results': results
            }
        
        elif report_type == 'detailed_observations':
            query = """
                SELECT b.name, obs.name, o.observation_date, ot.type_name, o.intensity
                FROM observations o
                JOIN black_holes b ON o.bh_id = b.bh_id
                JOIN observatories obs ON o.observatory_id = obs.observatory_id
                LEFT JOIN observation_types ot ON o.type_id = ot.type_id
                WHERE 1=1
            """
            params = []
            
            if bh_id:
                query += " AND o.bh_id = %s"
                params.append(bh_id)
            if observatory_id:
                query += " AND o.observatory_id = %s"
                params.append(observatory_id)
            if obs_type_id:
                query += " AND o.type_id = %s"
                params.append(obs_type_id)
            if start_date:
                query += " AND o.observation_date >= %s"
                params.append(start_date)
            if end_date:
                query += " AND o.observation_date <= %s"
                params.append(end_date)
                
            query += " ORDER BY o.observation_date DESC LIMIT 100;"
            
            cur.execute(query, params)
            results = cur.fetchall()
            dashboard_data = {
                'title': 'Detailed Observations',
                'columns': ['Black Hole', 'Observatory', 'Date', 'Type', 'Intensity'],
                'results': results
            }
        
        elif report_type == 'black_hole_summary':
            query = """
                SELECT b.name, b.classification, b.mass_solar_masses, 
                       b.distance_light_years, COUNT(o.obs_id) as observation_count
                FROM black_holes b
                LEFT JOIN observations o ON b.bh_id = o.bh_id
                WHERE 1=1
            """
            params = []
            
            if bh_id:
                query += " AND b.bh_id = %s"
                params.append(bh_id)
                
            query += " GROUP BY b.bh_id ORDER BY observation_count DESC;"
            
            cur.execute(query, params)
            results = cur.fetchall()
            dashboard_data = {
                'title': 'Black Hole Summary',
                'columns': ['Name', 'Classification', 'Mass (Solar M)', 'Distance (Light-years)', 'Observations'],
                'results': results
            }
    
    cur.close()
    conn.close()
    
    return render_template('custom_dashboard.html',
                          black_holes=black_holes,
                          observatories=observatories,
                          obs_types=obs_types,
                          dashboard_data=dashboard_data)


@app.route('/saved_dashboards')
def saved_dashboards():
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT dashboard_id, dashboard_name, report_type, description, created_at
            FROM saved_dashboards
            ORDER BY created_at DESC
        """)
        dashboards = cur.fetchall()
    except Exception as e:
        dashboards = []
        print(f"Error fetching dashboards: {str(e)}")
    
    cur.close()
    conn.close()
    
    return render_template('saved_dashboards.html', dashboards=dashboards)


@app.route('/load_dashboard/<int:dashboard_id>')
def load_dashboard(dashboard_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT report_type, bh_id, observatory_id, obs_type_id, start_date, end_date, dashboard_name
            FROM saved_dashboards
            WHERE dashboard_id = %s
        """, (dashboard_id,))
        dashboard = cur.fetchone()
        
        if not dashboard:
            cur.close()
            conn.close()
            flash('❌ Dashboard not found', 'danger')
            return redirect(url_for('saved_dashboards'))
        
        report_type, bh_id, observatory_id, obs_type_id, start_date, end_date, dashboard_name = dashboard
        
        cur.execute("SELECT bh_id, name FROM black_holes ORDER BY name;")
        black_holes = cur.fetchall()
        
        cur.execute("SELECT observatory_id, name FROM observatories ORDER BY name;")
        observatories = cur.fetchall()
        
        cur.execute("SELECT type_id, type_name FROM observation_types ORDER BY type_name;")
        obs_types = cur.fetchall()
        
        dashboard_data = generate_dashboard_report(report_type, bh_id, observatory_id, obs_type_id, start_date, end_date, cur, dashboard_name)
        
        cur.close()
        conn.close()
        
        flash('✅ Dashboard loaded successfully!', 'info')
        
        return render_template('custom_dashboard.html',
                              black_holes=black_holes,
                              observatories=observatories,
                              obs_types=obs_types,
                              dashboard_data=dashboard_data,
                              saved_dashboard_name=dashboard_name,
                              saved_dashboard_id=dashboard_id)
    
    except Exception as e:
        print(f"Error loading dashboard: {str(e)}")
        flash(f'❌ Error loading dashboard: {str(e)}', 'danger')
        cur.close()
        conn.close()
        return redirect(url_for('saved_dashboards'))


@app.route('/delete_dashboard/<int:dashboard_id>', methods=['POST'])
def delete_dashboard(dashboard_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM saved_dashboards WHERE dashboard_id = %s", (dashboard_id,))
        conn.commit()
        cur.close()
        conn.close()
        flash('✅ Dashboard deleted successfully!', 'success')
    except Exception as e:
        flash(f'❌ Error deleting dashboard: {str(e)}', 'danger')
        print(f"Error deleting dashboard: {str(e)}")
    
    return redirect(url_for('saved_dashboards'))


def generate_dashboard_report(report_type, bh_id, observatory_id, obs_type_id, start_date, end_date, cur, dashboard_name):
    if report_type == 'observations_by_bh':
        query = """
            SELECT b.name, COUNT(*) as count, AVG(o.intensity) as avg_intensity
            FROM observations o
            JOIN black_holes b ON o.bh_id = b.bh_id
            WHERE 1=1
        """
        params = []
        if bh_id:
            query += " AND o.bh_id = %s"
            params.append(bh_id)
        if start_date:
            query += " AND o.observation_date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND o.observation_date <= %s"
            params.append(end_date)
        query += " GROUP BY b.bh_id, b.name ORDER BY count DESC;"
        cur.execute(query, params)
        results = cur.fetchall()
        return {
            'title': f'{dashboard_name} - Observations by Black Hole',
            'columns': ['Black Hole', 'Observation Count', 'Avg Intensity'],
            'results': results
        }
    
    elif report_type == 'observations_by_observatory':
        query = """
            SELECT obs.name, COUNT(*) as count, AVG(o.intensity) as avg_intensity
            FROM observations o
            JOIN observatories obs ON o.observatory_id = obs.observatory_id
            WHERE 1=1
        """
        params = []
        if observatory_id:
            query += " AND o.observatory_id = %s"
            params.append(observatory_id)
        if start_date:
            query += " AND o.observation_date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND o.observation_date <= %s"
            params.append(end_date)
        query += " GROUP BY obs.observatory_id, obs.name ORDER BY count DESC;"
        cur.execute(query, params)
        results = cur.fetchall()
        return {
            'title': f'{dashboard_name} - Observations by Observatory',
            'columns': ['Observatory', 'Observation Count', 'Avg Intensity'],
            'results': results
        }
    
    elif report_type == 'observations_by_type':
        query = """
            SELECT ot.type_name, COUNT(*) as count, AVG(o.intensity) as avg_intensity
            FROM observations o
            LEFT JOIN observation_types ot ON o.type_id = ot.type_id
            WHERE 1=1
        """
        params = []
        if obs_type_id:
            query += " AND o.type_id = %s"
            params.append(obs_type_id)
        if start_date:
            query += " AND o.observation_date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND o.observation_date <= %s"
            params.append(end_date)
        query += " GROUP BY ot.type_id, ot.type_name ORDER BY count DESC;"
        cur.execute(query, params)
        results = cur.fetchall()
        return {
            'title': f'{dashboard_name} - Observations by Type',
            'columns': ['Observation Type', 'Count', 'Avg Intensity'],
            'results': results
        }
    
    elif report_type == 'detailed_observations':
        query = """
            SELECT b.name, obs.name, o.observation_date, ot.type_name, o.intensity
            FROM observations o
            JOIN black_holes b ON o.bh_id = b.bh_id
            JOIN observatories obs ON o.observatory_id = obs.observatory_id
            LEFT JOIN observation_types ot ON o.type_id = ot.type_id
            WHERE 1=1
        """
        params = []
        if bh_id:
            query += " AND o.bh_id = %s"
            params.append(bh_id)
        if observatory_id:
            query += " AND o.observatory_id = %s"
            params.append(observatory_id)
        if obs_type_id:
            query += " AND o.type_id = %s"
            params.append(obs_type_id)
        if start_date:
            query += " AND o.observation_date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND o.observation_date <= %s"
            params.append(end_date)
        query += " ORDER BY o.observation_date DESC LIMIT 100;"
        cur.execute(query, params)
        results = cur.fetchall()
        return {
            'title': f'{dashboard_name} - Detailed Observations',
            'columns': ['Black Hole', 'Observatory', 'Date', 'Type', 'Intensity'],
            'results': results
        }
    
    elif report_type == 'black_hole_summary':
        query = """
            SELECT b.name, b.classification, b.mass_solar_masses, 
                   b.distance_light_years, COUNT(o.obs_id) as observation_count
            FROM black_holes b
            LEFT JOIN observations o ON b.bh_id = o.bh_id
            WHERE 1=1
        """
        params = []
        if bh_id:
            query += " AND b.bh_id = %s"
            params.append(bh_id)
        query += " GROUP BY b.bh_id ORDER BY observation_count DESC;"
        cur.execute(query, params)
        results = cur.fetchall()
        return {
            'title': f'{dashboard_name} - Black Hole Summary',
            'columns': ['Name', 'Classification', 'Mass (Solar M)', 'Distance (Light-years)', 'Observations'],
            'results': results
        }
    
    return {'title': dashboard_name, 'columns': [], 'results': []}


if __name__ == '__main__':
    init_db()
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1', host='localhost',
            port=int(os.environ.get('PORT', '5000')))