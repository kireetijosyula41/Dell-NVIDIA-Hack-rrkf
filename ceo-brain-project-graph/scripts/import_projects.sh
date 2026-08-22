#!/usr/bin/env bash
set -euo pipefail

until mongosh "mongodb://mongodb:27017/admin" --quiet --eval 'db.runCommand({ ping: 1 }).ok' >/dev/null 2>&1; do
  sleep 1
done

mongoimport --uri "mongodb://mongodb:27017/ceo_brain" --collection projects --jsonArray --drop --file /seed/projects.json
mongoimport --uri "mongodb://mongodb:27017/ceo_brain" --collection emails --jsonArray --drop --file /seed/emails.json
mongoimport --uri "mongodb://mongodb:27017/ceo_brain" --collection project_relationships --jsonArray --drop --file /seed/project_relationships.json
mongoimport --uri "mongodb://mongodb:27017/ceo_brain" --collection project_domains --jsonArray --drop --file /seed/project_domains.json

mongosh "mongodb://mongodb:27017/ceo_brain" --quiet --eval '
  db.projects.createIndex({ projectId: 1 }, { unique: true });
  db.projects.createIndex({ domains: 1 });
  db.emails.createIndex({ projectId: 1, date: -1 });
  db.emails.createIndex({ labels: 1 });
  db.project_relationships.createIndex({ fromProject: 1, toProject: 1, relationType: 1 }, { unique: true });
  db.project_relationships.createIndex({ fromProject: 1 });
  db.project_relationships.createIndex({ toProject: 1 });
'
