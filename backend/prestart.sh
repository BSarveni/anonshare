#!/bin/bash
set -e

alembic upgrade head
python init_db.py
