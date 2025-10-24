# tasks.py
import ast
import pandas as pd
from celery import Celery
from massql import msql_engine

from utils import gnps2_get_libray_dataframe_wrapper, download_and_filter_mgf

# Connect to Redis (broker) and store results back in Redis
celery_app = Celery(
    "streamlit-massql-post-mn_tasks",
    broker="redis://streamlit-massql-post-mn-redis",
    backend="redis://streamlit-massql-post-mn-redis"
)

celery_app.conf.update(
    result_expires=900,              # 0.25 hour expiration for results (prevents Redis bloat)
)

@celery_app.task()
def heartbeat_task():
    return "Post-mn worker is alive."

@celery_app.task(bind=True)
def download_and_process_mgf_task(self, task_id):
    """
    Download library matches and MGF files for a given GNPS2 task.
    
    Args:
        task_id: GNPS2 task ID
        
    Returns:
        dict with:
            - library_matches: DataFrame as dict
            - cleaned_mgf_path: str
            - all_scans: list
            - pepmass_list: list
    """
    try:
        # Update progress
        self.update_state(state='PROGRESS', meta={'current': 0, 'total': 2, 'status': 'Downloading library matches...'})
        
        # Download library matches
        library_matches = gnps2_get_libray_dataframe_wrapper(task_id)
        
        # Update progress
        self.update_state(state='PROGRESS', meta={'current': 1, 'total': 2, 'status': 'Downloading and filtering MGF file...'})
        
        # Download and filter MGF
        cleaned_mgf_path, all_scans, pepmass_list = download_and_filter_mgf(task_id)
        
        return {
            'library_matches': library_matches.to_dict(),
            'cleaned_mgf_path': cleaned_mgf_path,
            'all_scans': all_scans,
            'pepmass_list': pepmass_list
        }
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise

@celery_app.task(bind=True)
def run_massql_query_task(self, query_name, query_string, mgf_path):
    """
    Run a single MassQL query on an MGF file.
    
    Args:
        query_name: Name of the query
        query_string: MassQL query string
        mgf_path: Path to the MGF file
        
    Returns:
        dict with:
            - query: query name
            - scan_list: list of matching scan numbers (as int)
    """
    try:
        self.update_state(state='PROGRESS', meta={'status': f'Running query: {query_name}'})
        
        results_df = msql_engine.process_query(query_string, mgf_path)
        
        if len(results_df) == 0:
            return {'query': query_name, 'scan_list': []}
        else:
            passed_scan_ls = results_df['scan'].values.tolist()
            passed_scan_ls = [int(x) for x in passed_scan_ls]
            return {'query': query_name, 'scan_list': passed_scan_ls}
            
    except KeyError:
        # Handle case where query returns no results
        return {'query': query_name, 'scan_list': []}
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e), 'query': query_name})
        raise

@celery_app.task(bind=True)
def run_all_massql_queries_task(self, custom_queries, mgf_path):
    """
    Run all MassQL queries on an MGF file (using a group for parallel execution).
    
    Args:
        custom_queries: dict of {query_name: query_string}
        mgf_path: Path to the MGF file
        
    Returns:
        list of dicts with query results
    """
    from celery import group
    
    try:
        total_queries = len(custom_queries)
        self.update_state(
            state='PROGRESS', 
            meta={'current': 0, 'total': total_queries, 'status': 'Starting queries...'}
        )
        
        # Create a group of query tasks to run in parallel
        job = group(
            run_massql_query_task.s(query_name, query_string, mgf_path)
            for query_name, query_string in custom_queries.items()
        )
        
        # Execute all queries in parallel
        result = job.apply_async()
        results = result.get()
        
        return results
        
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise