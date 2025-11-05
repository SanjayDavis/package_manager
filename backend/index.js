const express = require('express');
const cors = require('cors');
const bcrypt = require('bcrypt');
const mysql = require('mysql2/promise');
const jwt = require('jsonwebtoken');
const axios = require('axios');
const zlib = require('zlib');
require('dotenv').config();

const app = express();
app.use(cors());
app.use(express.json());

const SECRET_KEY = process.env.JWT_SECRET || 'your_jwt_secret';

const pool = mysql.createPool({
  host: process.env.MYSQL_HOST,
  user: process.env.MYSQL_USER,
  password: process.env.MYSQL_PASSWORD,
  database: process.env.MYSQL_DB,
});

// Register endpoint
app.post('/register', async (req, res) => {
  const { username, password, role = 'user' } = req.body;
  try {
    const hashed = await bcrypt.hash(password, 10);
    await pool.execute(
      "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
      [username, hashed, role]
    );
    res.status(201).json({ message: 'User registered' });
  } catch (error) {
    if (error.code === 'ER_DUP_ENTRY') {
      res.status(409).json({ error: 'Username already exists' });
    } else {
      res.status(500).json({ error: 'Server error' });
    }
  }
});

// Login endpoint - only allow admins to login via frontend
app.post('/login', async (req, res) => {
  const { username, password } = req.body;
  try {
    const [rows] = await pool.execute('SELECT id, password_hash, role FROM users WHERE username = ?', [username]);
    if (rows.length === 0) return res.status(401).json({ error: 'Invalid credentials' });

    const user = rows[0];
    if (user.role !== 'admin') {
      return res.status(403).json({ error: 'Access denied: only admins allowed on frontend' });
    }

    const match = await bcrypt.compare(password, user.password_hash);
    if (!match) return res.status(401).json({ error: 'Invalid credentials' });

    const token = jwt.sign({ userId: user.id, role: user.role }, SECRET_KEY, { expiresIn: '1h' });
    res.json({ token, role: user.role });
  } catch (error) {
    res.status(500).json({ error: 'Server error' });
  }
});

// CLI Login endpoint - allows regular users
app.post('/login-cli', async (req, res) => {
  const { username, password } = req.body;
  try {
    const [rows] = await pool.execute('SELECT id, password_hash, role FROM users WHERE username = ?', [username]);
    if (rows.length === 0) return res.status(401).json({ error: 'Invalid credentials' });

    const user = rows[0];
    
    const match = await bcrypt.compare(password, user.password_hash);
    if (!match) return res.status(401).json({ error: 'Invalid credentials' });

    const token = jwt.sign({ userId: user.id, role: user.role }, SECRET_KEY, { expiresIn: '30d' });
    res.json({ token, role: user.role, username: username });
  } catch (error) {
    res.status(500).json({ error: 'Server error' });
  }
});

// JWT Authentication middleware
function authenticateToken(req, res, next) {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];
  if (!token) return res.sendStatus(401);
  jwt.verify(token, SECRET_KEY, (err, user) => {
    if (err) return res.sendStatus(403);
    req.user = user;
    next();
  });
}

// Packages API
app.get('/api/packages', authenticateToken, async (req, res) => {
  const search = req.query.search?.trim() || '';
  const page = parseInt(req.query.page) || 1;
  const limit = 100;
  const offset = (page - 1) * limit;

  try {
    let rows, total;
    
    if (search && search.length > 0) {
      const searchExact = search;
      const searchStart = `${search}%`;
      const searchContains = `%${search}%`;
      
      [rows] = await pool.query(
        `SELECT id, name, version, architecture, filename,
         CASE 
           WHEN name = ? THEN 1
           WHEN name LIKE ? THEN 2
           ELSE 3
         END as relevance
         FROM packages 
         WHERE name LIKE ? 
         ORDER BY relevance, name ASC 
         LIMIT ? OFFSET ?`,
        [searchExact, searchStart, searchContains, limit, offset]
      );
      
      [[{ total }]] = await pool.query(
        "SELECT COUNT(*) as total FROM packages WHERE name LIKE ?",
        [searchContains]
      );
    } else {
      [rows] = await pool.query(
        "SELECT id, name, version, architecture, filename FROM packages ORDER BY name ASC LIMIT ? OFFSET ?",
        [limit, offset]
      );
      [[{ total }]] = await pool.query(
        "SELECT COUNT(*) as total FROM packages"
      );
    }

    res.json({
      data: rows,
      total,
      page,
      totalPages: Math.ceil(total / limit)
    });
  } catch (error) {
    console.error('Error fetching packages:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

// Update Package API - Admin only
app.put('/api/packages/:id', authenticateToken, async (req, res) => {
  if (req.user.role !== 'admin') {
    return res.status(403).json({ error: 'Access denied: Admin only' });
  }

  const packageId = req.params.id;
  const { name, version, architecture, filename } = req.body;

  // Validate input
  if (!name || !version || !architecture || !filename) {
    return res.status(400).json({ error: 'All fields are required' });
  }

  try {
    // Check if package exists and verify name hasn't changed
    const [existing] = await pool.query('SELECT id, name FROM packages WHERE id = ?', [packageId]);
    if (existing.length === 0) {
      return res.status(404).json({ error: 'Package not found' });
    }

    // Prevent changing package name
    if (existing[0].name !== name) {
      return res.status(400).json({ error: 'Package name cannot be changed' });
    }

    // Update package (only version, architecture, filename)
    await pool.query(
      'UPDATE packages SET version = ?, architecture = ?, filename = ? WHERE id = ?',
      [version, architecture, filename, packageId]
    );

    res.json({ 
      message: 'Package updated successfully',
      package: { id: packageId, name, version, architecture, filename }
    });
  } catch (error) {
    console.error('Error updating package:', error);
    if (error.code === 'ER_DUP_ENTRY') {
      res.status(409).json({ error: 'A package with this name and version already exists' });
    } else {
      res.status(500).json({ error: 'Server error' });
    }
  }
});

// Add Package API - Admin only
app.post('/api/packages', authenticateToken, async (req, res) => {
  if (req.user.role !== 'admin') {
    return res.status(403).json({ error: 'Access denied: Admin only' });
  }

  const { name, version, architecture, filename, dependencies } = req.body;

  // Validate input
  if (!name || !version || !architecture || !filename) {
    return res.status(400).json({ error: 'All fields are required' });
  }

  const conn = await pool.getConnection();
  
  try {
    await conn.beginTransaction();

    // Insert new package
    const [result] = await conn.query(
      'INSERT INTO packages (name, version, architecture, filename) VALUES (?, ?, ?, ?)',
      [name, version, architecture, filename]
    );

    const packageId = result.insertId;

    // Insert dependencies if provided
    if (dependencies && Array.isArray(dependencies) && dependencies.length > 0) {
      for (const dep of dependencies) {
        if (dep.name) {
          await conn.query(
            'INSERT INTO dependencies (package_id, dependency_name, version_constraint) VALUES (?, ?, ?)',
            [packageId, dep.name, dep.version_constraint || null]
          );
        }
      }
    }

    await conn.commit();

    res.status(201).json({ 
      message: `Package added successfully with ${dependencies?.length || 0} dependencies`,
      package: { id: packageId, name, version, architecture, filename, dependencies: dependencies || [] }
    });
  } catch (error) {
    await conn.rollback();
    console.error('Error adding package:', error);
    if (error.code === 'ER_DUP_ENTRY') {
      res.status(409).json({ error: 'A package with this name and version already exists' });
    } else {
      res.status(500).json({ error: 'Server error' });
    }
  } finally {
    conn.release();
  }
});

// Delete Package API - Admin only
app.delete('/api/packages/:id', authenticateToken, async (req, res) => {
  if (req.user.role !== 'admin') {
    return res.status(403).json({ error: 'Access denied: Admin only' });
  }

  const packageId = req.params.id;

  try {
    // Check if package exists
    const [existing] = await pool.query('SELECT id, name FROM packages WHERE id = ?', [packageId]);
    if (existing.length === 0) {
      return res.status(404).json({ error: 'Package not found' });
    }

    // Delete dependencies first (foreign key constraint)
    await pool.query('DELETE FROM dependencies WHERE package_id = ?', [packageId]);
    
    // Delete package
    await pool.query('DELETE FROM packages WHERE id = ?', [packageId]);

    res.json({ 
      message: 'Package and its dependencies deleted successfully',
      deletedPackage: existing[0].name
    });
  } catch (error) {
    console.error('Error deleting package:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

// Dependencies API
app.get('/api/dependencies', authenticateToken, async (req, res) => {
  const search = req.query.search?.trim() || '';
  const page = parseInt(req.query.page) || 1;
  const limit = 100;
  const offset = (page - 1) * limit;

  try {
    let rows, total;
    
    if (search && search.length > 0) {
      const searchContains = `%${search}%`;
      
      [rows] = await pool.query(
        `SELECT p.name as package_name, d.dependency_name, d.version_constraint 
         FROM dependencies d 
         JOIN packages p ON d.package_id = p.id 
         WHERE p.name LIKE ? OR d.dependency_name LIKE ? 
         ORDER BY p.name ASC 
         LIMIT ? OFFSET ?`,
        [searchContains, searchContains, limit, offset]
      );
      
      [[{ total }]] = await pool.query(
        `SELECT COUNT(*) as total 
         FROM dependencies d 
         JOIN packages p ON d.package_id = p.id 
         WHERE p.name LIKE ? OR d.dependency_name LIKE ?`,
        [searchContains, searchContains]
      );
    } else {
      [rows] = await pool.query(
        `SELECT p.name as package_name, d.dependency_name, d.version_constraint 
         FROM dependencies d 
         JOIN packages p ON d.package_id = p.id 
         ORDER BY p.name ASC 
         LIMIT ? OFFSET ?`,
        [limit, offset]
      );
      [[{ total }]] = await pool.query(
        `SELECT COUNT(*) as total FROM dependencies`
      );
    }

    res.json({
      data: rows,
      total,
      page,
      totalPages: Math.ceil(total / limit)
    });
  } catch (error) {
    console.error('Error fetching dependencies:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

// PackageDownloads API
app.get('/api/packagedownloads', authenticateToken, async (req, res) => {
  const search = req.query.search?.trim() || '';
  const page = parseInt(req.query.page) || 1;
  const limit = 100;
  const offset = (page - 1) * limit;

  try {
    let rows, total;
    
    if (search && search.length > 0) {
      const searchContains = `%${search}%`;
      
      try {
        [rows] = await pool.query(
          "SELECT * FROM packagedownloads WHERE user_id LIKE ? OR package_name LIKE ? ORDER BY download_timestamp DESC LIMIT ? OFFSET ?",
          [searchContains, searchContains, limit, offset]
        );
        [[{ total }]] = await pool.query(
          "SELECT COUNT(*) as total FROM packagedownloads WHERE user_id LIKE ? OR package_name LIKE ?",
          [searchContains, searchContains]
        );
      } catch (err) {
        rows = [];
        total = 0;
      }
    } else {
      try {
        [rows] = await pool.query(
          "SELECT * FROM packagedownloads ORDER BY download_timestamp DESC LIMIT ? OFFSET ?",
          [limit, offset]
        );
        [[{ total }]] = await pool.query(
          "SELECT COUNT(*) as total FROM packagedownloads"
        );
      } catch (err) {
        rows = [];
        total = 0;
      }
    }

    res.json({
      data: rows,
      total,
      page,
      totalPages: Math.ceil(total / limit)
    });
  } catch (error) {
    console.error('Error fetching downloads:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

// Log download endpoint
app.post('/api/log-download', authenticateToken, async (req, res) => {
  const {
    user_id,
    package_name,
    version,
    download_duration_seconds,
    install_duration_seconds,
    client_ip,
    download_status,
    install_status
  } = req.body;

  try {
    await pool.query(
      `INSERT INTO packagedownloads 
       (user_id, package_name, version, download_duration_seconds, 
        install_duration_seconds, client_ip, download_status, install_status) 
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
      [user_id, package_name, version, download_duration_seconds,
       install_duration_seconds, client_ip, download_status, install_status]
    );
    res.json({ message: 'Download logged successfully' });
  } catch (error) {
    console.error('Error logging download:', error);
    res.status(500).json({ error: 'Failed to log download' });
  }
});

// Helper function to parse Packages file format
function parsePackagesFile(content) {
  const packages = [];
  const dependencies = [];

  const entries = content.split('\n\n');
  entries.forEach(entry => {
    const lines = entry.split('\n');
    const pkg = {};
    lines.forEach(line => {
      const [key, ...rest] = line.split(': ');
      if (!key) return;
      const value = rest.join(': ');

      switch (key) {
        case 'Package':
          pkg.name = value;
          break;
        case 'Version':
          pkg.version = value;
          break;
        case 'Architecture':
          pkg.architecture = value;
          break;
        case 'Filename':
          pkg.filename = value;
          break;
        case 'Depends':
          const deps = value.split(',').map(s => s.trim());
          deps.forEach(dep => {
            const match = dep.match(/^([^\s(]+)(?:\s*\(([^)]+)\))?/);
            if (match) {
              dependencies.push({ 
                package_name: pkg.name, 
                depends_on: match[1],
                version_constraint: match[2] || null
              });
            }
          });
          break;
      }
    });

    if (pkg.name) {
      packages.push(pkg);
    }
  });

  return { packages, dependencies };
}

// Update packages endpoint
// Update packages endpoint
// Update packages endpoint - WITH PROGRESS FEEDBACK
app.post('/api/update-packages', authenticateToken, async (req, res) => {
  if (req.user.role !== 'admin') {
    return res.status(403).json({ error: 'Access denied' });
  }

  try {
    console.log('\n=== Package Update Started ===');
    console.log('Time:', new Date().toLocaleString());
    
    // Ubuntu 24.04 (Noble) repositories
    const repos = [
      {
        name: 'Main Repository',
        url: 'http://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/Packages.gz'
      },
      {
        name: 'Universe Repository',
        url: 'http://archive.ubuntu.com/ubuntu/dists/noble/universe/binary-amd64/Packages.gz'
      }
    ];

    let allPackages = [];
    let allDependencies = [];

    for (const repo of repos) {
      console.log(`\n[${repo.name}]`);
      console.log(`Downloading from ${repo.url}...`);
      
      const startTime = Date.now();
      const response = await axios.get(repo.url, { 
        responseType: 'arraybuffer',
        onDownloadProgress: (progressEvent) => {
          const totalLength = progressEvent.total;
          if (totalLength !== null) {
            const progress = Math.round((progressEvent.loaded * 100) / totalLength);
            process.stdout.write(`\rProgress: ${progress}% (${(progressEvent.loaded / 1024 / 1024).toFixed(2)} MB / ${(totalLength / 1024 / 1024).toFixed(2)} MB)`);
          }
        }
      });
      
      const downloadTime = ((Date.now() - startTime) / 1000).toFixed(2);
      const sizeInMB = (response.data.length / 1024 / 1024).toFixed(2);
      console.log(`\n✓ Downloaded successfully (${sizeInMB} MB in ${downloadTime}s)`);
      
      console.log('Decompressing...');
      const decompressStart = Date.now();
      const decompressed = zlib.gunzipSync(response.data).toString('utf-8');
      const decompressTime = ((Date.now() - decompressStart) / 1000).toFixed(2);
      console.log(`✓ Decompressed in ${decompressTime}s`);
      
      console.log('Parsing packages...');
      const parseStart = Date.now();
      const { packages, dependencies } = parsePackagesFile(decompressed);
      const parseTime = ((Date.now() - parseStart) / 1000).toFixed(2);
      console.log(`✓ Parsed ${packages.length} packages with ${dependencies.length} dependencies in ${parseTime}s`);
      
      allPackages = allPackages.concat(packages);
      allDependencies = allDependencies.concat(dependencies);
    }

    console.log('\n--- Database Update ---');
    console.log(`Total packages to insert: ${allPackages.length}`);
    console.log(`Total dependencies to insert: ${allDependencies.length}`);

    const conn = await pool.getConnection();

    try {
      await conn.beginTransaction();
      console.log('Transaction started');

      console.log('Clearing old data...');
      await conn.query('DELETE FROM dependencies');
      await conn.query('DELETE FROM packages');
      console.log('✓ Old data cleared');

      console.log('Inserting packages...');
      const packageStartTime = Date.now();
      const packageIdMap = {};
      let insertedPackages = 0;
      
      for (const pkg of allPackages) {
        const [result] = await conn.query(
          'INSERT INTO packages (name, version, architecture, filename) VALUES (?, ?, ?, ?)',
          [pkg.name, pkg.version, pkg.architecture, pkg.filename]
        );
        packageIdMap[pkg.name] = result.insertId;
        insertedPackages++;
        
        // Progress every 1000 packages
        if (insertedPackages % 1000 === 0) {
          const progress = ((insertedPackages / allPackages.length) * 100).toFixed(1);
          process.stdout.write(`\rInserting packages: ${progress}% (${insertedPackages}/${allPackages.length})`);
        }
      }
      const packageTime = ((Date.now() - packageStartTime) / 1000).toFixed(2);
      console.log(`\n✓ Inserted ${insertedPackages} packages in ${packageTime}s`);

      console.log('Inserting dependencies...');
      const depStartTime = Date.now();
      let insertedDeps = 0;
      
      for (const dep of allDependencies) {
        const packageId = packageIdMap[dep.package_name];
        if (packageId) {
          await conn.query(
            'INSERT INTO dependencies (package_id, dependency_name, version_constraint) VALUES (?, ?, ?)',
            [packageId, dep.depends_on, dep.version_constraint]
          );
          insertedDeps++;
          
          // Progress every 5000 dependencies
          if (insertedDeps % 5000 === 0) {
            const progress = ((insertedDeps / allDependencies.length) * 100).toFixed(1);
            process.stdout.write(`\rInserting dependencies: ${progress}% (${insertedDeps}/${allDependencies.length})`);
          }
        }
      }
      const depTime = ((Date.now() - depStartTime) / 1000).toFixed(2);
      console.log(`\n✓ Inserted ${insertedDeps} dependencies in ${depTime}s`);

      console.log('Committing transaction...');
      await conn.commit();
      console.log('✓ Transaction committed successfully');
      
      const successMessage = `Updated ${allPackages.length} packages and ${allDependencies.length} dependencies from Ubuntu 24.04 (Noble)`;
      console.log('\n=== Update Completed Successfully ===');
      console.log(successMessage);
      console.log('Time:', new Date().toLocaleString());
      console.log('===================================\n');
      
      res.json({ status: successMessage });
    } catch (err) {
      await conn.rollback();
      console.error('✗ Transaction failed, rolling back...');
      throw err;
    } finally {
      conn.release();
    }

  } catch (error) {
    console.error('\n✗ Error updating packages:', error.message);
    res.status(500).json({ error: 'Failed to update packages' });
  }
});



const PORT = process.env.PORT || 8000;
const HOST = '0.0.0.0';

app.listen(PORT, HOST, () => {
  console.log(`Backend listening on ${HOST}:${PORT}`);
});
