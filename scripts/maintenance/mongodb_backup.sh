#!/bin/bash
# MongoDB Backup and Restore Script
# Handles both mongodump (binary) and JSON export

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$SCRIPT_DIR/backups/mongodb"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
MONGO_PASSWORD="${MONGO_PASSWORD:-changeme123}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

function log_info() {
    echo -e "${GREEN}ℹ${NC} $1"
}

function log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

function log_error() {
    echo -e "${RED}✗${NC} $1"
}

function log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

function check_mongodb_running() {
    if ! docker ps | grep -q dinner-menu-mongodb; then
        log_error "MongoDB container is not running"
        echo "Start it with: docker compose up -d mongodb"
        exit 1
    fi
}

function backup_json() {
    log_info "Creating JSON backup..."
    
    local backup_file="$BACKUP_DIR/recipes_${TIMESTAMP}.json"
    mkdir -p "$BACKUP_DIR"
    
    # Export recipes collection to JSON
    docker exec dinner-menu-api python3 -c "
import json
from db import RecipeDB
from bson import ObjectId
from datetime import datetime

def json_serial(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f'Type {type(obj)} not serializable')

db = RecipeDB()
recipes = list(db.get_all_recipes())
print(json.dumps(recipes, indent=2, default=json_serial))
" > "$backup_file"
    
    local size=$(du -h "$backup_file" | cut -f1)
    local count=$(grep -c '"_id"' "$backup_file" || echo "0")
    
    log_success "JSON backup created: $backup_file"
    log_info "  Size: $size"
    log_info "  Recipes: $count"
    
    echo "$backup_file"
}

function backup_mongodump() {
    log_info "Creating binary backup with mongodump..."
    
    local backup_path="$BACKUP_DIR/dump_${TIMESTAMP}"
    mkdir -p "$backup_path"
    
    # Run mongodump inside MongoDB container
    docker exec dinner-menu-mongodb mongodump \
        --username=admin \
        --password="$MONGO_PASSWORD" \
        --authenticationDatabase=admin \
        --db=dinner_menu \
        --out=/tmp/backup 2>&1 | grep -v "WARNING" || true
    
    # Copy backup out of container
    docker cp dinner-menu-mongodb:/tmp/backup/dinner_menu "$backup_path/"
    
    # Clean up inside container
    docker exec dinner-menu-mongodb rm -rf /tmp/backup
    
    local size=$(du -sh "$backup_path" | cut -f1)
    
    log_success "Binary backup created: $backup_path"
    log_info "  Size: $size"
    
    echo "$backup_path"
}

function restore_json() {
    local backup_file="$1"
    
    if [ ! -f "$backup_file" ]; then
        log_error "Backup file not found: $backup_file"
        exit 1
    fi
    
    log_warn "This will restore recipes from: $backup_file"
    echo -n "Continue? (yes/no): "
    read confirm
    
    if [ "$confirm" != "yes" ] && [ "$confirm" != "y" ]; then
        log_info "Cancelled"
        exit 0
    fi
    
    log_info "Restoring from JSON backup..."
    
    # Copy file into container and restore
    docker cp "$backup_file" dinner-menu-api:/tmp/restore.json
    
    docker exec dinner-menu-api python3 -c "
import json
from db import RecipeDB
from datetime import datetime
from bson import ObjectId

db = RecipeDB()

with open('/tmp/restore.json', 'r') as f:
    recipes = json.load(f)

# Clear existing recipes
count = db.collection.count_documents({})
print(f'Removing {count} existing recipes...')
db.collection.delete_many({})

# Insert restored recipes
inserted = 0
for recipe in recipes:
    # Remove _id if present (let MongoDB generate new ones)
    if '_id' in recipe:
        del recipe['_id']
    
    # Convert date strings back to datetime if needed
    if 'created_at' in recipe and isinstance(recipe['created_at'], str):
        recipe['created_at'] = datetime.fromisoformat(recipe['created_at'])
    if 'updated_at' in recipe and isinstance(recipe['updated_at'], str):
        recipe['updated_at'] = datetime.fromisoformat(recipe['updated_at'])
    
    db.collection.insert_one(recipe)
    inserted += 1

print(f'✓ Restored {inserted} recipes')
"
    
    # Clean up
    docker exec dinner-menu-api rm /tmp/restore.json
    
    log_success "Restore complete"
}

function restore_mongodump() {
    local backup_path="$1"
    
    if [ ! -d "$backup_path" ]; then
        log_error "Backup directory not found: $backup_path"
        exit 1
    fi
    
    log_warn "This will restore recipes from: $backup_path"
    echo -n "Continue? (yes/no): "
    read confirm
    
    if [ "$confirm" != "yes" ] && [ "$confirm" != "y" ]; then
        log_info "Cancelled"
        exit 0
    fi
    
    log_info "Restoring from binary backup..."
    
    # Copy backup into container
    docker cp "$backup_path/dinner_menu" dinner-menu-mongodb:/tmp/restore/
    
    # Run mongorestore
    docker exec dinner-menu-mongodb mongorestore \
        --username=admin \
        --password="$MONGO_PASSWORD" \
        --authenticationDatabase=admin \
        --db=dinner_menu \
        --drop \
        /tmp/restore/dinner_menu 2>&1 | grep -v "WARNING" || true
    
    # Clean up
    docker exec dinner-menu-mongodb rm -rf /tmp/restore
    
    log_success "Restore complete"
}

function list_backups() {
    log_info "Available backups:\n"
    
    if [ -d "$BACKUP_DIR" ]; then
        echo "JSON Backups:"
        find "$BACKUP_DIR" -name "recipes_*.json" -type f | while read file; do
            local size=$(du -h "$file" | cut -f1)
            local date=$(basename "$file" | sed 's/recipes_\(.*\)\.json/\1/')
            local count=$(grep -c '"_id"' "$file" 2>/dev/null || echo "0")
            echo "  - $(basename $file) ($size, $count recipes)"
        done
        
        echo -e "\nBinary Backups:"
        find "$BACKUP_DIR" -name "dump_*" -type d | while read dir; do
            local size=$(du -sh "$dir" | cut -f1)
            local date=$(basename "$dir" | sed 's/dump_//')
            echo "  - $(basename $dir) ($size)"
        done
    else
        log_warn "No backups found in $BACKUP_DIR"
    fi
}

function show_usage() {
    cat << EOF
MongoDB Backup and Restore Script

Usage: $0 <command> [options]

Commands:
  backup [--json|--dump|--both]   Create a backup (default: both)
  restore <backup_file>            Restore from a backup
  list                             List available backups
  help                             Show this help message

Examples:
  $0 backup                        # Create both JSON and binary backups
  $0 backup --json                 # Create only JSON backup
  $0 restore backups/mongodb/recipes_20260119_123456.json
  $0 list                          # List all available backups

Backup locations:
  JSON:   $BACKUP_DIR/recipes_YYYYMMDD_HHMMSS.json
  Binary: $BACKUP_DIR/dump_YYYYMMDD_HHMMSS/

EOF
}

# Main script
case "${1:-}" in
    backup)
        check_mongodb_running
        
        echo "╔════════════════════════════════════════════════════════════════╗"
        echo "║              MongoDB Backup                                    ║"
        echo "╚════════════════════════════════════════════════════════════════╝"
        echo
        
        backup_type="${2:---both}"
        
        if [ "$backup_type" == "--json" ] || [ "$backup_type" == "--both" ]; then
            backup_json
            echo
        fi
        
        if [ "$backup_type" == "--dump" ] || [ "$backup_type" == "--both" ]; then
            backup_mongodump
            echo
        fi
        
        log_success "Backup complete!"
        ;;
        
    restore)
        check_mongodb_running
        
        if [ -z "${2:-}" ]; then
            log_error "Please specify a backup file or directory"
            echo "Usage: $0 restore <backup_file_or_dir>"
            exit 1
        fi
        
        backup_path="$2"
        
        echo "╔════════════════════════════════════════════════════════════════╗"
        echo "║              MongoDB Restore                                   ║"
        echo "╚════════════════════════════════════════════════════════════════╝"
        echo
        
        if [ -f "$backup_path" ] && [[ "$backup_path" == *.json ]]; then
            restore_json "$backup_path"
        elif [ -d "$backup_path" ]; then
            restore_mongodump "$backup_path"
        else
            log_error "Invalid backup: $backup_path"
            exit 1
        fi
        ;;
        
    list)
        echo "╔════════════════════════════════════════════════════════════════╗"
        echo "║              MongoDB Backups                                   ║"
        echo "╚════════════════════════════════════════════════════════════════╝"
        echo
        list_backups
        ;;
        
    help|--help|-h)
        show_usage
        ;;
        
    *)
        log_error "Unknown command: ${1:-}"
        echo
        show_usage
        exit 1
        ;;
esac
