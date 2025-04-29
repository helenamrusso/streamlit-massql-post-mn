#!/bin/bash

source activate py39
streamlit run app.py --server.port 5000 --server.address 0.0.0.0