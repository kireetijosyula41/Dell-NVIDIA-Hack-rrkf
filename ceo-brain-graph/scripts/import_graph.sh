#!/usr/bin/env bash
set -euo pipefail

until mongosh "mongodb://mongodb:27017/admin" --quiet --eval 'db.runCommand({ ping: 1 }).ok' >/dev/null 2>&1; do
  sleep 1
done

mongoimport --uri "mongodb://mongodb:27017/ceo_brain" --collection repositories --jsonArray --drop --file /seed/repositories.json
mongoimport --uri "mongodb://mongodb:27017/ceo_brain" --collection relationships --jsonArray --drop --file /seed/relationships.json
mongoimport --uri "mongodb://mongodb:27017/ceo_brain" --collection domains --jsonArray --drop --file /seed/domains.json

mongosh "mongodb://mongodb:27017/ceo_brain" --quiet --eval '
  db.repositories.createIndex({ repoId: 1 }, { unique: true });
  db.repositories.createIndex({ domains: 1 });
  db.relationships.createIndex({ fromRepo: 1, toRepo: 1, relationType: 1 }, { unique: true });
  db.relationships.createIndex({ fromRepo: 1 });
  db.relationships.createIndex({ toRepo: 1 });
  db.relationships.createIndex({ relationType: 1, confidence: -1 });
  db.domains.createIndex({ id: 1 }, { unique: true });
'
