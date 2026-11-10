# 🌌 Black Hole Observation Tracker

A comprehensive web application for managing and analyzing astronomical observations of black holes from observatories worldwide. Built as a full-featured database management system demonstrating enterprise-level features including stored procedures, database triggers, audit logging, and advanced analytics.

## What This Does

This application centralizes black hole observation data from multiple sources - ground telescopes, space observatories, and gravitational wave detectors like LIGO. Instead of scattered data across different systems, everything lives in one searchable, analyzable database with a beautiful space-themed interface.

Users can record observations, search by multiple criteria, track gravitational wave events, generate analytical reports, and build custom dashboards - all while the system automatically maintains an audit trail of every change.

## Features

### Core Functionality
- **Complete CRUD Operations** - Full create, read, update, and delete functionality across all 7 database tables
- **Advanced Search with Filters** - Search black holes by name (partial matching), mass range, distance range, and classification
- **Smart Reference Tables** - Search page displays all available black holes so users know what to search for
- **Custom Dashboard Builder** - Create personalized reports with flexible filtering by black hole, observatory, observation type, and date ranges
- **Saved Dashboards** - Save dashboard configurations and reload them anytime for reproducible analysis
- **Pre-built Analytics Reports** - Six comprehensive reports using PostgreSQL stored procedures for optimal performance
- **Automatic Audit Logging** - Database triggers track every UPDATE and DELETE operation with before/after snapshots
- **Multi-Layer Input Validation** - Client-side HTML5 validation, server-side Python checks, and database constraints prevent invalid data
- **User-Friendly Notifications** - Success and error messages displayed as animated pop-up alerts
- **Readable Forms** - High-contrast white backgrounds with black text for easy data entry

### Data You Can Manage

**Black Holes:**
- Name, mass (solar masses), distance (light-years)
- Classification (Stellar, Supermassive, Intermediate)
- Discovery year and method
- Celestial coordinates (Right Ascension, Declination)

**Observations:**
- Black hole being observed
- Observatory making the observation
- Observation date and type (X-ray, Radio, Optical, etc.)
- Wavelength range and intensity measurements
- Notes and additional metadata

**Observatories:**
- Facility name and location
- Observatory type and operational dates
- Links to all observations made by that facility

**Gravitational Wave Events:**
- Event designation (e.g., GW150914)
- Two merging black holes
- Individual and final masses
- Energy released during merger

**Supporting Data:**
- Observation types with descriptions
- Wavelength ranges across electromagnetic spectrum
- Discovery methods with historical context

### Advanced Database Features

**Stored Procedures (3):**
- `get_most_observed_bh(limit)` - Ranks black holes by observation count
- `get_avg_intensity_per_bh()` - Calculates average intensity per black hole
- `get_observations_by_type()` - Groups observations by type for distribution analysis

**Database Triggers (2):**
- Automatic audit logging on black_holes table (UPDATE/DELETE)
- Automatic audit logging on observations table (UPDATE/DELETE)
- Captures complete row state as JSON before and after changes

**Database Event Functions:**
- `cleanup_old_audit_logs()` - Removes audit entries older than 90 days
- Ready for scheduled execution with pg_cron

**Secondary Indexes (7):**
- Optimized for common query patterns
- Each index includes detailed performance justification in comments
- Targets foreign keys, date ranges, and search fields

## Tech Stack

**Backend:**
- Python 3.8+
- Flask 2.0+ (web framework)
- PostgreSQL 12+ (database)
- psycopg2-binary 2.9+ (database driver)

**Frontend:**
- HTML5 with semantic markup
- CSS3 with custom animations
- Bootstrap 5.3 (responsive framework)
- Vanilla JavaScript (no heavy frameworks)
- Animated space GIF backgrounds

**Database Architecture:**
- 7 normalized tables in Third Normal Form (3NF)
- 2 support tables (audit_log, saved_dashboards)
- Foreign keys with CASCADE and SET NULL operations
- CHECK constraints for data integrity
- UNIQUE constraints preventing duplicates
- Comprehensive comments documenting design decisions

## Getting Started

### Prerequisites

Install these before proceeding:

1. **Python 3.8 or higher**
   - Download: https://www.python.org/downloads/
   - Verify: `python --version` or `python3 --version`

2. **PostgreSQL 12 or higher**
   - Download: https://www.postgresql.org/download/
   - Verify: `psql --version`
   - **Important:** Remember the password you set for the `postgres` user during installation

3. **pip (Python package manager)**
   - Usually included with Python
   - Verify: `pip --version`

### Installation Steps

#### 1. Clone the Repository

```bash
git clone https://github.com/Rhea-Thomas/Blackhole-Tracker.git
cd Blackhole-Tracker
```

The layout:

```
Blackhole-Tracker/
├── app.py                       # Flask app, schema, stored procedures, routes
├── black_hole_tracker_dump.sql  # Full database dump (alternative to auto-init)
├── .env.example                 # Settings template
├── requirements.txt
├── templates/                   # Jinja2 pages (CRUD, search, reports, dashboards)
└── static/                      # Background images and screenshots
```

#### 2. Create PostgreSQL Database

**Option A - Using psql command line:**
```bash
# Windows Command Prompt or Mac/Linux Terminal
psql -U postgres

# Inside psql:
CREATE DATABASE black_hole_tracker;
\q
```

**Option B - Using pgAdmin (GUI):**
1. Open pgAdmin
2. Right-click "Databases" → Create → Database
3. Name: `black_hole_tracker`
4. Click Save

#### 3. Configure the Database Connection

Credentials are read from environment variables, so no password lives in the code. Copy the template and fill in your PostgreSQL password:

```bash
cp .env.example .env    # .env is git-ignored
# then edit .env and set DB_PASSWORD (and FLASK_SECRET_KEY)
```

| Variable | Default | Purpose |
|---|---|---|
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `DB_NAME` | `black_hole_tracker` | Database name |
| `DB_USER` | `postgres` | Database user |
| `DB_PASSWORD` | *(empty)* | Your PostgreSQL password |
| `FLASK_SECRET_KEY` | random per run | Signs session cookies; set it so sessions survive restarts |
| `FLASK_DEBUG` | off | Set to `1` for auto-reload and debug pages |
| `PORT` | `5000` | Port the app listens on |

You can also `export DB_PASSWORD=...` in your shell instead of using a `.env` file.

#### 4. Install Python Dependencies

Open terminal/command prompt in the project directory:

```bash
pip install -r requirements.txt
```

If you get permission errors, try:
```bash
pip install --user -r requirements.txt
```

**Required packages:**
- **flask** - Web framework for routing and templating
- **psycopg2-binary** - PostgreSQL database adapter
- **python-dotenv** - Loads settings from `.env`

#### 5. Initialize Database

**The database will initialize automatically** when you first run the application. The `init_db()` function creates all tables, indexes, triggers, stored procedures, and loads sample data.

**Alternative:** If you prefer to initialize manually using the SQL dump file:
```bash
psql -U postgres -d black_hole_tracker -f black_hole_tracker_dump.sql
```

#### 6. Run the Application

From the project directory:

```bash
python app.py
```

You should see output like:
```
Database initialized successfully!
 * Running on http://127.0.0.1:5000
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment.
```

#### 7. Access the Application

Open your web browser and navigate to:
```
http://localhost:5000
```

You should see the Black Hole Observation Tracker homepage with six feature cards.

### Troubleshooting

**Problem:** `ModuleNotFoundError: No module named 'flask'`
- **Solution:** Install Flask: `pip install flask`

**Problem:** `ModuleNotFoundError: No module named 'psycopg2'`
- **Solution:** Install psycopg2: `pip install psycopg2-binary`

**Problem:** `psycopg2.OperationalError: FATAL: password authentication failed`
- **Solution:** Check that `DB_PASSWORD` in your `.env` (or shell) matches your PostgreSQL password

**Problem:** `psycopg2.OperationalError: could not connect to server`
- **Solution:** Ensure PostgreSQL service is running:
  - **Windows:** Services → postgresql-x64-[version] should be "Running"
  - **Mac:** `brew services start postgresql`
  - **Linux:** `sudo service postgresql start`

**Problem:** Port 5000 already in use
- **Solution:** Either:
  - Close the application using port 5000, or
  - Set a different port: `PORT=5001 python app.py`

**Problem:** Database initialization errors
- **Solution:** 
  1. Drop and recreate database: `DROP DATABASE black_hole_tracker; CREATE DATABASE black_hole_tracker;`
  2. Restart application

**Problem:** Forms showing white text on white background (can't read)
- **Solution:** Ensure you're using the updated `base.html` with the new CSS for `.form-control` and `.form-label`

### Verifying Installation

After launching, verify everything works:

1. **Homepage loads** - You should see 6 feature cards
2. **View Data** - Click "View Data" → Should show table of observations
3. **Search works** - Click "Search & Filter" → Should see reference table of black holes
4. **Reports generate** - Click "Analytics & Reports" → Should display 6 different reports
5. **Add observation** - Click "Add Observation" → Form should have readable white inputs
6. **Success message** - After adding, you should see green "✅ Observation added successfully!" popup

## How to Use

### Adding Your First Observation

1. Click **"Add Observation"** from the homepage
2. Select a black hole from the dropdown (e.g., "Cygnus X-1")
3. Select an observatory (e.g., "Chandra X-ray Observatory")
4. Choose observation date (cannot be in the future)
5. Select observation type (e.g., "X-ray")
6. Optionally select wavelength range
7. Enter intensity measurement
8. Add any notes
9. Click **"Submit Observation"**
10. You'll see a green success message and be redirected to the observations list

### Searching for Black Holes

1. Click **"Search & Filter"**
2. Review the reference table showing all available black holes
3. Enter search criteria:
   - **Name:** Partial matching (e.g., "Cygnus" finds both Cygnus X-1 and V404 Cygni)
   - **Mass Range:** Min and/or max in solar masses
   - **Distance Range:** Min and/or max in light-years
   - **Classification:** Dropdown filter
4. Click **"Search Black Holes"**
5. Results display in a sortable table

### Building Custom Dashboards

1. Click **"Custom Dashboard"**
2. Select report type from dropdown
3. Choose filters (optional):
   - Specific black hole
   - Specific observatory
   - Observation type
   - Date range
4. Click **"Generate"**
5. Review results
6. To save for later:
   - Enter dashboard name
   - Add description (optional)
   - Click **"Save Dashboard"**
7. See green "✅ Dashboard saved successfully!" message

### Loading Saved Dashboards

1. Click **"Saved Dashboards"**
2. Browse list of previously saved dashboards
3. Click **"Load"** next to desired dashboard
4. Dashboard regenerates with original filters
5. Can modify and re-save if needed

### Viewing Analytics Reports

1. Click **"Analytics & Reports"**
2. Six reports automatically generate:
   - **Most Observed Black Holes** (uses stored procedure)
   - **Observations by Observatory**
   - **Black Hole Classification Summary**
   - **Gravitational Wave Events**
   - **Observation Types Distribution** (uses stored procedure)
   - **Average Intensity per Black Hole** (uses stored procedure)
3. All reports display on one page
4. Scroll to review different analyses

### Editing Records

All entity types support editing:

1. Navigate to the entity list page (e.g., "Observations")
2. Click yellow **"Edit"** button next to the record
3. Form loads with current values
4. Modify any fields
5. Click **"Update"**
6. Database trigger automatically logs the change to audit_log
7. See green success message

### Deleting Records

1. Navigate to the entity list page
2. Click red **"Delete"** button
3. Confirm deletion in popup dialog
4. Database trigger logs the deletion
5. CASCADE operations automatically handle related records:
   - Deleting a black hole removes all its observations
   - Deleting an observatory sets observations.observatory_id to NULL
6. See green "✅ Deleted successfully!" message

## Sample Data Included

The system initializes with realistic astronomical data:

**8 Black Holes:**
- Cygnus X-1 (14.8 solar masses, 6,070 light-years)
- M87* (6.5 million solar masses, 53 million light-years)
- Sagittarius A* (4 million solar masses, 26,000 light-years)
- TON 618 (66 million solar masses, 18.2 billion light-years)
- ULAS J1342+0928 (800 million solar masses, 13.1 billion light-years)
- V404 Cygni (9 solar masses, 7,800 light-years)
- GRS 1915+105 (12 solar masses, 36,000 light-years)
- Mrk 421 (300 million solar masses, 400 million light-years)

**6 Observatories:**
- Chandra X-ray Observatory (Space-based, X-ray, operational since 1999)
- Event Horizon Telescope (Global network, Radio, operational since 2015)
- LIGO (USA, Gravitational Wave, operational since 2015)
- Virgo (Italy, Gravitational Wave, operational since 2007)
- Hubble Space Telescope (Space-based, Optical, operational since 1990)
- NuSTAR (Space-based, X-ray, operational since 2012)

**3 Gravitational Wave Events:**
- GW150914 (First detected black hole merger, September 14, 2015)
- GW170814 (Three-detector observation, August 14, 2017)
- GW190412 (Asymmetric mass merger, April 12, 2019)

**30+ Observations:**
- Distributed across all black holes
- Various observation types (X-ray, Radio, Optical, Infrared)
- Spanning the past year
- Realistic intensity measurements

## Database Architecture

### Schema Design (3rd Normal Form)

The database follows strict normalization principles with 7 primary tables:

1. **discovery_methods** - Lookup table for detection techniques
2. **observation_types** - Categories of observations (X-ray, Radio, etc.)
3. **wavelength_ranges** - Electromagnetic spectrum classifications
4. **observatories** - Telescope facilities worldwide
5. **black_holes** - Core entity with physical properties
6. **observations** - Junction table connecting black holes to observatories
7. **gravitational_wave_events** - Black hole merger records

Plus 2 support tables:
- **audit_log** - Automatic change tracking (populated by triggers)
- **saved_dashboards** - User dashboard configurations

### Key Relationships

- **One-to-Many:** discovery_methods → black_holes
- **One-to-Many:** black_holes → observations (CASCADE delete)
- **One-to-Many:** observatories → observations (SET NULL on delete)
- **One-to-Many:** observation_types → observations (SET NULL on delete)
- **One-to-Many:** wavelength_ranges → observations (SET NULL on delete)
- **Two One-to-Many:** black_holes → gravitational_wave_events (self-referencing for merger pairs)

### Constraints and Integrity

**Primary Keys:** All tables use auto-incrementing SERIAL primary keys

**Foreign Keys:** All foreign keys include explicit CASCADE behavior:
- `ON DELETE CASCADE` - For critical relationships (black holes → observations)
- `ON DELETE SET NULL` - For optional relationships (observatory → observations)
- `ON UPDATE CASCADE` - Propagates ID changes automatically

**CHECK Constraints:** Enforce business rules:
- Mass and distance must be positive
- Discovery year between 1600 and 2025
- Right Ascension: 0-360°, Declination: -90° to +90°
- Wavelength min < max
- Observation dates cannot be in the future
- Intensity values non-negative

**UNIQUE Constraints:** Prevent duplicates on:
- Black hole names
- Observatory names
- Discovery method names
- Observation type names
- Wavelength range names

## Performance Optimizations

### Secondary Indexes

Seven strategically placed indexes optimize query performance:

1. **idx_observations_bh_id** - JOIN operations between observations and black_holes
2. **idx_observations_observatory_id** - Observatory-based filtering
3. **idx_observations_date** - Date range queries in dashboard builder
4. **idx_observations_type_id** - Grouping by observation type
5. **idx_black_holes_classification** - Classification filtering in search
6. **idx_black_holes_name** - Text search with ILIKE pattern matching
7. **idx_audit_log_date** - Audit trail queries and cleanup operations

Each index includes detailed comments justifying its existence and explaining expected performance improvements.

### Stored Procedures

Complex analytical queries moved to database level for:
- Reduced network traffic (results computed server-side)
- Better query optimization by PostgreSQL engine
- Cleaner Python code (no complex GROUP BY logic)
- Reusability across multiple routes

## Design Decisions

### Why Flask?
Lightweight and unopinionated - perfect for database-focused applications. Easy to learn but powerful enough for complex routing. Jinja2 templating integrates seamlessly with Bootstrap.

### Why PostgreSQL?
- Superior support for advanced features (stored procedures, triggers, complex queries)
- Excellent documentation and community support
- ACID compliance crucial for scientific data integrity
- Handles CASCADE operations elegantly
- PL/pgSQL language for stored procedures

### Why Stored Procedures?
Moving analytical logic to the database:
- Improves performance (database optimizes better than application code)
- Reduces code duplication (one procedure, many routes can call it)
- Encapsulates business logic close to the data
- Simplifies testing (procedures can be tested independently)

### Why Space Theme?
An application tracking black holes deserves an interface that reflects its subject matter. The dark theme with animated space backgrounds creates an immersive experience appropriate for astronomical data. Plus it looks professional while being visually distinct from generic database interfaces.

### CASCADE vs. SET NULL Design

The application uses two different foreign key deletion strategies:

**CASCADE (black holes → observations):**
- If a black hole is deleted, its observations become meaningless
- Automatic deletion maintains data integrity
- Example: Deleting Cygnus X-1 removes all 5 of its observations

**SET NULL (observatories → observations):**
- If an observatory is decommissioned, historical observations remain valuable
- Setting observatory_id to NULL preserves the observation while marking facility as unavailable
- Example: Deleting Chandra keeps observations but marks them as from "unknown observatory"

This dual approach balances data integrity with historical preservation.

## Known Limitations

**Authentication:**
- Single-user application with no login system
- All users have full administrative access
- Not suitable for multi-user deployment without adding authentication

**Data Export:**
- Results viewable only in web interface
- No CSV, JSON, or PDF export functionality
- Users cannot download data for external analysis

**Pagination:**
- All list views load complete datasets
- Performance degrades with thousands of records
- Production deployment would need LIMIT/OFFSET pagination

**Visualization:**
- Reports use tables, not charts/graphs
- No visual representations of trends
- Missing time-series plots or distribution histograms

**Scheduled Jobs:**
- `cleanup_old_audit_logs()` function exists but isn't scheduled
- Would require pg_cron extension for automatic execution
- Currently must be called manually

**Mobile Optimization:**
- Responsive layout works on mobile but isn't optimized
- Forms can be difficult to fill on small screens
- Some tables require horizontal scrolling on phones

## Future Enhancements

### Short-Term (1-3 months)
- **Chart.js Integration** - Add visualizations to reports page
- **CSV Export** - Download search results and reports
- **Pagination** - Handle large datasets efficiently
- **Advanced Search** - Boolean logic (AND/OR combinations)
- **Bulk Upload** - Import observations from CSV files

### Medium-Term (3-6 months)
- **User Authentication** - Login system with role-based permissions
- **REST API** - Enable external systems to submit observations
- **Real-Time Data** - Automated imports from astronomical databases
- **Mobile App** - iOS/Android companion applications
- **Email Notifications** - Alerts for significant events

### Long-Term (6-12 months)
- **Machine Learning** - Anomaly detection in observations
- **Collaborative Features** - Multi-user annotation and discussions
- **Predictive Analytics** - Suggest promising observation targets
- **Integration with Telescope Systems** - Direct data feeds from observatories

## Technical Learning Outcomes

Building this project provided hands-on experience with:

**Database Design:**
- Normalization theory applied to real-world data
- Understanding when to use CASCADE vs SET NULL
- Designing for both integrity and usability

**PostgreSQL Advanced Features:**
- Writing stored procedures in PL/pgSQL
- Creating triggers for automatic audit logging
- Implementing CHECK constraints for data validation
- Strategic index placement for performance

**Web Development:**
- Flask routing and request handling
- Jinja2 templating with inheritance
- Form processing and validation
- Error handling and user feedback

**Software Engineering:**
- Iterative development and refactoring
- Code organization and modularity
- User experience design
- Documentation and commenting practices

## Testing the System

### Quick Feature Test

1. **Add Observation:**
   - Navigate to "Add Observation"
   - Fill form completely
   - Submit → Should see green success message
   - Check "View Data" → New observation appears

2. **Search:**
   - Go to "Search & Filter"
   - See reference table with 8 black holes
   - Search for "Cygnus" → Should find 2 results
   - Try mass range 1,000,000 to 10,000,000 → Should find supermassive holes

3. **Edit Record:**
   - In "View Data", click "Edit" on any observation
   - Change intensity value
   - Update → Green success message
   - Check audit_log table: `SELECT * FROM audit_log;` → Should show the change

4. **Custom Dashboard:**
   - Go to "Custom Dashboard"
   - Select "Observations by Black Hole"
   - Set date range for 2024
   - Generate → See results
   - Save dashboard → Success message
   - Go to "Saved Dashboards" → Your dashboard appears

5. **Reports:**
   - Click "Analytics & Reports"
   - All 6 reports should display with data
   - Verify stored procedures are being called

### Database Verification

Connect to PostgreSQL and run:

```sql
-- Check table counts
SELECT 'black_holes' AS table_name, COUNT(*) FROM black_holes
UNION ALL SELECT 'observations', COUNT(*) FROM observations
UNION ALL SELECT 'observatories', COUNT(*) FROM observatories;

-- Verify triggers exist
SELECT tgname, tgtype FROM pg_trigger 
WHERE tgrelid IN ('black_holes'::regclass, 'observations'::regclass);

-- Check indexes
SELECT tablename, indexname FROM pg_indexes 
WHERE schemaname = 'public' ORDER BY tablename;

-- Test stored procedures
SELECT * FROM get_most_observed_bh(5);
SELECT * FROM get_observations_by_type();

-- Verify audit logging (after making a change)
SELECT * FROM audit_log ORDER BY changed_at DESC LIMIT 5;
```

## Credits and Acknowledgments

**Data Sources:**
- Black hole physical properties inspired by NASA/ESA astronomical databases
- Observatory information from public sources (NASA, ESO, LIGO)
- Gravitational wave event data based on LIGO/Virgo published results
- Sample masses and distances approximate real measurements

**Technical Resources:**
- PostgreSQL Documentation
- Flask Documentation
- Bootstrap Framework
- Stack Overflow community

**Course:**
- CS5200 Database Management Systems
- Northeastern University
- Fall 2024

## License

This is an academic project developed for educational purposes. Free to use for learning and demonstration.

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Verify all prerequisites are installed
3. Ensure PostgreSQL service is running
4. Confirm `DB_PASSWORD` is set correctly in `.env`

 

**Built with ☕, curiosity about the universe, and a lot of database normalization**