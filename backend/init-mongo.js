db.createUser({
    user: process.env.MONGO_ROOT_USERNAME,
    pwd: process.env.MONGO_ROOT_PASSWORD,
    roles: [
      {
        role: "readWrite",
        db: "infocal"
      }
    ]
  });
  
  db.createCollection("users");
  db.createCollection("warnings");
  db.createCollection("warning_history");
  
  // Create indexes
  db.users.createIndex({ "email": 1 }, { unique: true });
  db.warnings.createIndex({ "warning_id": 1 }, { unique: true });
  db.warning_history.createIndex({ "user_email": 1, "warning_id": 1 }, { unique: true });
