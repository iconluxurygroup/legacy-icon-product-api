from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from celery.result import AsyncResult
from mylib.logic import (hello_world,hello_nik)
from tasks.celery_helper import fetch_task_result
from models.endpoint_io_models import RequestData#,Task
from tasks.celery_back_tasks import create_task


from tasks.celery_helper_image import fetch_task_result_image
from tasks.celery_back_tasks_image import create_task_image,execute_workflow_cms


app = FastAPI(title="Icon Product Api")

# CORS Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)
# Define a router for user-related operations
sample_router = APIRouter()
msrp_router = APIRouter()
image_router = APIRouter()
image_routerV2 = APIRouter()
# Define a router for product-related operations


@sample_router.get("/")
def root():
    return {"message": "Hello World API use /hello_world or /hello_nik/yourname for a personalized message :)"}
        
@sample_router.get("/hello_nik/{name}")
async def hello_nik_api(name: str):
    return {"message": hello_nik(name)}

@sample_router.get("/hello_world")
async def hello_world_api():
    return {"message": hello_world()}

@msrp_router.post('/create')
async def send_product(requestData:RequestData):
    task_id = create_task.delay(requestData.dataset_split)
    return {'task_id': str(task_id), 'status': 'Processing'}

@msrp_router.get("/poll/{task_id}")
async def poll_task(task_id: str):
    result = fetch_task_result(task_id)
    if result['status'] == 'Processing':
        return {'status': 'Processing'}
    elif result['status'] == 'Completed':
        if 'task_name' in result['result']:
            return result['result']
        else:
            return {'status': 'Completed', 'result': result['result']}
    else:
        raise HTTPException(status_code=500, detail="Unexpected task status")
#!!!!!!!!!!!!!!!!!!!!!!!!    
@image_router.post('/create')
async def send_product(requestData:RequestData):
    task_id = create_task_image.delay(requestData.dataset_split)
    return {'task_id': str(task_id), 'status': 'Processing'}
# @image_router.post('/create_cms')
# async def send_product(requestData:RequestData):
#     task_id = create_task_image_cms.delay(requestData.dataset_split)
#     return {'task_id': str(task_id), 'status': 'Processing'}
@image_routerV2.post('/create_cms')
async def send_product(requestData: RequestData):
    task_id = execute_workflow_cms(*requestData.dataset_split)
    if task_id:
        return {'task_id': task_id, 'status': 'Processing'}
    else:
        raise HTTPException(status_code=400, detail="Failed to start the workflow")
@image_router.get("/poll/{task_id}")
async def poll_task(task_id: str):
    result = fetch_task_result_image(task_id)
    if result['status'] == 'Processing':
        return {'status': 'Processing'}
    elif result['status'] == 'Completed':
        return {'status': 'Completed', 'result': result['result']}
    else:
        raise HTTPException(status_code=500, detail="Unexpected task status")    
@image_routerV2.get('/status/{task_id}')
async def get_status(task_id: str):
    result = AsyncResult(task_id)
    if result.ready():
        if result.successful():
            return {'status': 'Complete', 'result': result.get()}
        else:
            return {'status': 'Failed', 'result': None}
    else:
        return {'status': 'Processing'}

@image_routerV2.get('/results/{task_id}')
async def get_results(task_id: str):
    result = AsyncResult(task_id)
    if result.ready():
        return {'status': 'Complete', 'data': result.get()}
    return {'status': 'Still Processing'}
    
app.include_router(sample_router, prefix="/api/v1/sample")
app.include_router(msrp_router, prefix="/api/v1/msrp")
app.include_router(image_router, prefix="/api/v1/image")
app.include_router(image_routerV2, prefix="/api/v2/image")



if __name__ == "__main__":
    #LOCAL WITH RELOAD
    #uvicorn.run("main:app", port=8080 ,host='0.0.0.0',reload=True)
    #production
    uvicorn.run(app, port=8080 ,host='0.0.0.0')