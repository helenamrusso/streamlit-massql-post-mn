#!/bin/bash

source activate py39
celery -A tasks worker --loglevel=INFO --autoscale=10,1 --max-tasks-per-child=5
