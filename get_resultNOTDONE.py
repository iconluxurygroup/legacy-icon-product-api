###OGGG 
def fetch_task_result(task_id):
    task_result = AsyncResult(task_id, app=celery_app)
    if not task_result.ready():
        return None  # or consider raising an exception or returning a status indicating it's still processing
    
    result = task_result.get()  # This might be a single result or a list containing more task IDs
    if isinstance(result, list):
        # Assuming result format is similar to the one provided: [[task_id, [subtask_results]], status]
        # Adjust the parsing logic based on your actual result structure
        final_results = []
        for item in result:
            if isinstance(item, list) and item:  # Check if the first item is a list with content
                subtask_id = item[0]
                if subtask_id is not None:
                    # Recursively fetch results of subtasks
                    subtask_result = fetch_task_result(subtask_id)
                    final_results.append(subtask_result)
                else:
                    # Handle case where there's no more subtask IDs, and we have final data
                    final_results.append(item)
        return final_results
    else:
        # Directly return the result if it's not a list implying no further nested tasks
        return result
    


def fetch_task_result_with_retry(task_id, max_attempts=10, delay=5, timeout=60):
    """
    Fetch task result, retrying until the task completes or a timeout is reached.
    
    :param task_id: The ID of the task to fetch.
    :param max_attempts: Maximum number of attempts to check the task's status.
    :param delay: Delay between checks in seconds.
    :param timeout: Maximum time to wait for task completion in seconds.
    :return: The result of the task or a timeout status.
    """
    start_time = time.time()
    attempts = 0
    
    while attempts < max_attempts and time.time() - start_time < timeout:
        result = fetch_task_result(task_id)
        if result is not None and 'status' in result and result['status'] != 'Processing':
            return result
        time.sleep(delay)
        attempts += 1
    
    return {'status': 'Failed', 'error': 'Task did not complete within the given timeout or max attempts.'}

def fetch_task_result(task_id):
    task_result = AsyncResult(task_id, app=celery_app)
    if not task_result.ready():
        return {'status': 'Processing', 'task_id': task_id}
    
    result = task_result.get()
    if isinstance(result, dict) and 'price' not in result:
        # Handle case where 'price' is not in result, indicating it might still be processing
        return {'status': 'Processing', 'task_id': task_id}
    return result