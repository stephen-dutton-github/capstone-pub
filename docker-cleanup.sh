#!/bin/bash

echo "🧼 Starting Docker cleanup..."

# Remove unused build cache (all, not just dangling)
echo "🔧 Pruning build cache..."
docker builder prune -af

# Remove unused volumes
echo "🗃 Pruning unused volumes..."
docker volume prune -f

# Remove stopped containers, unused images, and networks
echo "🗑 Running full system prune..."
docker system prune -af --volumes

# Optional: Clean up dangling images (if any remain)
# echo "🧹 Cleaning dangling images..."
# docker image prune -f

echo "✅ Docker cleanup complete!"
