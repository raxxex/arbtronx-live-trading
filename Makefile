# CEX Arbitrage Bot Makefile

.PHONY: help install setup test run dashboard frontend clean lint format

# Default target
help:
	@echo "CEX Arbitrage Bot - Available Commands:"
	@echo ""
	@echo "Setup Commands:"
	@echo "  install     - Install Python dependencies"
	@echo "  setup       - Complete setup (install + configure)"
	@echo "  frontend    - Install frontend dependencies"
	@echo ""
	@echo "Run Commands:"
	@echo "  run         - Start the arbitrage bot"
	@echo "  dashboard   - Start the dashboard backend"
	@echo "  dev         - Start both bot and dashboard"
	@echo "  start       - Interactive startup script"
	@echo ""
	@echo "Development Commands:"
	@echo "  test        - Run test suite"
	@echo "  lint        - Run code linting"
	@echo "  format      - Format code"
	@echo "  clean       - Clean temporary files"
	@echo ""
	@echo "Utility Commands:"
	@echo "  logs        - View recent logs"
	@echo "  status      - Check bot status"

# Setup commands
install:
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt

setup: install
	@echo "Setting up environment..."
	@if [ ! -f .env ]; then \
		cp .env.template .env; \
		echo "Created .env file from template"; \
		echo "Please edit .env with your configuration"; \
	fi
	@mkdir -p logs data
	@echo "Setup complete!"

frontend:
	@echo "Installing frontend dependencies..."
	cd src/dashboard/frontend && npm install

# Run commands
run:
	@echo "Starting CEX Arbitrage Bot..."
	python main.py

dashboard:
	@echo "Starting dashboard backend..."
	python -m src.dashboard.backend.app

dev:
	@echo "Starting development environment..."
	@echo "Dashboard will be available at http://localhost:8000"
	@echo "Press Ctrl+C to stop"
	python -m src.dashboard.backend.app &
	sleep 2
	python main.py

start:
	@echo "Starting interactive setup..."
	python start.py

# Development commands
test:
	@echo "Running test suite..."
	pytest -v

test-coverage:
	@echo "Running tests with coverage..."
	pytest --cov=src tests/ --cov-report=html

lint:
	@echo "Running code linting..."
	flake8 src/ tests/ --max-line-length=100
	mypy src/ --ignore-missing-imports

format:
	@echo "Formatting code..."
	black src/ tests/ main.py start.py config.py
	@echo "Code formatted!"

clean:
	@echo "Cleaning temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	@echo "Cleanup complete!"

# Utility commands
logs:
	@echo "Recent bot logs:"
	@if [ -f logs/arbitrage_bot.log ]; then \
		tail -50 logs/arbitrage_bot.log; \
	else \
		echo "No log file found"; \
	fi

status:
	@echo "Checking bot status..."
	@curl -s http://localhost:8000/api/status | python -m json.tool || echo "Bot not running or dashboard not accessible"

# Docker commands (if using Docker)
docker-build:
	@echo "Building Docker image..."
	docker build -t cex-arbitrage-bot .

docker-run:
	@echo "Running Docker container..."
	docker run -d --name arbitrage-bot -p 8000:8000 --env-file .env cex-arbitrage-bot

docker-stop:
	@echo "Stopping Docker container..."
	docker stop arbitrage-bot
	docker rm arbitrage-bot

# Database commands
db-init:
	@echo "Initializing database..."
	python -c "import asyncio; from src.database.models import init_database; asyncio.run(init_database())"

db-reset:
	@echo "Resetting database..."
	rm -f arbitrage_bot.db
	$(MAKE) db-init

# Backup commands
backup:
	@echo "Creating backup..."
	@mkdir -p backups
	@cp arbitrage_bot.db backups/arbitrage_bot_$(shell date +%Y%m%d_%H%M%S).db
	@echo "Backup created in backups/ directory"

# Installation verification
verify:
	@echo "Verifying installation..."
	@python -c "import ccxt, fastapi, sqlalchemy; print('✓ Core dependencies installed')"
	@python -c "from src.exchanges.base import BaseExchange; print('✓ Exchange modules working')"
	@python -c "from src.arbitrage.calculator import ArbitrageCalculator; print('✓ Arbitrage engine working')"
	@if [ -f .env ]; then echo "✓ Environment file exists"; else echo "✗ Environment file missing"; fi
	@echo "Verification complete!"

# Quick start for new users
quickstart: setup verify
	@echo ""
	@echo "🚀 Quick Start Complete!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Edit .env file with your API keys"
	@echo "2. Run 'make start' for interactive startup"
	@echo "3. Or run 'make run' to start the bot directly"
	@echo ""
	@echo "For help: make help"
