.PHONY: run dev health

# Default target starts the archive computation with caffeinate to prevent sleep
run: health
	OMP_THREAD_LIMIT=1 caffeinate -i uv run python main.py archive

# Start the dashboard in dev mode
dev:
	cd dashboard && npm run dev -- -p 3000

# Check if dashboard is active before running
health:
	@curl -s http://localhost:3000/api/health | grep -q "ok" || (echo "[ERROR] Dashboard is not running on port 3000. Please run 'make dev' first." && exit 1)
	@echo "[OK] dashboard is healthy."

# Cleanup all local cached images for all issues
cleanup-all:
	rm -rf data/generated/images/*
	rm -rf data/generated/ocr/*
	rm -rf data/output/*
	@echo "[OK] All local cache cleaned up."

# Start fresh: cleanup GCS and local data
reset:
	uv run python main.py reset
	make cleanup-all

# Clean up Python artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .ruff_cache
	@echo "[OK] Python artifacts cleaned up."
