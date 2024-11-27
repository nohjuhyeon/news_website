from fastapi import FastAPI               
app = FastAPI()
from typing import Optional

from databases.connections import Settings,Database
from beanie import PydanticObjectId
import datetime
from bson.errors import InvalidId  # 이 부분 추가
from typing import List
from fastapi import Query
from datetime import datetime,timedelta
settings = Settings()
@app.on_event("startup")
async def init_db():
    await settings.initialize_database()


# from routes.admin import router as admin_router                   

from fastapi import Request                                
from fastapi.templating import Jinja2Templates              
# from utils.paginations import Paginations

from models.report_list import report_list
collection_report_list = Database(report_list)
from models.g2b_notice_list import g2b_notice_list
collection_g2b_notice_list = Database(g2b_notice_list)
from models.news_list import news_list
collection_news_list = Database(news_list)
from fastapi.middleware.cors import CORSMiddleware             
app.add_middleware(
    CORSMiddleware,            
    allow_origins=["*"],  
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles
# # url 경로(url에서 입력해야 하는 주소), 자원 물리 경로(directory; 실제 경로), 프로그래밍 측면(key의 이름 지정)
# app.mount("/css", StaticFiles(directory="resources/css/"), name="static_css")
# app.mount("/images", StaticFiles(directory="resources/images/"), name="static_images")

# 정적 파일 마운트
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates/")    


@app.get("/news/") # 펑션 호출 방식
@app.get("/news/{page_number}") # 펑션 호출 방식
async def list_get(request:Request, page_number: Optional[int]=1,search_type: Optional[str]=None,keyword: Optional[str]=None,category: List[str] = Query(None)):
    await request.form()
    conditions = {} 
    if keyword and search_type:
        conditions[search_type] = {"$regex": keyword, "$options": "i"}
    if category:
        conditions["category"] = {"$in": category}
    total_list_pagination, pagination = await collection_news_list.getsbyconditionswithpagination(conditions
                                                                     ,page_number,'news_date')
    return templates.TemplateResponse(name="news_list.html", context={'request':request,
                                                                 'items':total_list_pagination,
                                                                 'pagination':pagination,
                                                                 'search_type':search_type,
                                                                 'keyword':keyword,
                                                                 'selected_category':category or []})

@app.get("/report/") # 펑션 호출 방식
@app.get("/report/{page_number}") # 펑션 호출 방식
async def list_get(request:Request, page_number: Optional[int]=1,search_type: Optional[str]=None,keyword: Optional[str]=None,category: List[str] = Query(None)):
    await request.form()
    conditions = {} 
    if keyword and search_type:
        conditions[search_type] = {"$regex": keyword, "$options": "i"}  # i는 대소문자 구분 없음
    if category:
        conditions["category"] = {"$in": category}
    
    total_list_pagination, pagination = await collection_report_list.getsbyconditionswithpagination(conditions
                                                                     ,page_number,'start_date')
    
    return templates.TemplateResponse("report_list.html",context={'request':request,
                                                                'items':total_list_pagination,
                                                                'pagination':pagination,
                                                                'search_type':search_type,
                                                                 'keyword':keyword,
                                                                'selected_category':category or []})


@app.get("/g2b_notice/") # 펑션 호출 방식
@app.get("/g2b_notice/{page_number}") # 펑션 호출 방식
async def list_get(request:Request, page_number: Optional[int]=1,search_type: Optional[str]=None,keyword: Optional[str]=None,notice_class: List[str] = Query(None),notice_type: List[str] = Query(None)):
    await request.form()
    conditions = {} 
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    today_str = today.strftime("%Y/%m/%d")
    yesterday_str = yesterday.strftime("%Y/%m/%d")

    if keyword and search_type:
        # 검색 조건 추가
        conditions[search_type] = {"$regex": keyword, "$options": "i"}  # i는 대소문자 구분 없음
    
    if notice_class:
        conditions["notice_class"] = {"$in": notice_class}
    
    if notice_type:
        conditions["type"] = {"$in": notice_type}
    
    
    total_list_pagination, pagination = await collection_g2b_notice_list.getsbyconditionswithpagination(conditions
                                                                     ,page_number,'start_date')
    
    return templates.TemplateResponse("g2b_notice.html", {
        "request": request,
        "items": total_list_pagination,
        "pagination": pagination,
        "search_type": search_type,
        "keyword": keyword,
        "selected_notice_classes": notice_class or [],
        "selected_notice_types": notice_type or [],
        'today':today_str,
        'yesterday':yesterday_str,
        
    })



# 기존 import문 아래에 추가
from fastapi import HTTPException
from beanie import PydanticObjectId

# 뉴스 상세 페이지 라우트 추가

@app.get("/news_detail/{news_id}")
async def news_detail(request: Request, news_id: str,search_type: Optional[str]=None,keyword: Optional[str]=None,category: List[str] = Query(None)):
    try:
        # 문자열 ID를 PydanticObjectId로 변환
        object_id = PydanticObjectId(news_id)
        
        # 현재 뉴스 조회
        news = await collection_news_list.get(object_id)

        
        if news is None:
            raise HTTPException(status_code=404, detail="News not found")
        
        # 현재 뉴스의 날짜 가져오기
        current_date = news.news_date
        prev_conditions = {"news_date": {"$gt": current_date},"_id": {"$ne": object_id}}
        next_conditions = {"news_date": {"$lt": current_date},"_id": {"$ne": object_id}}
        if keyword and search_type:
            prev_conditions[search_type] = {"$regex": keyword, "$options": "i"}
            next_conditions[search_type] = {"$regex": keyword, "$options": "i"}
        if category:
            prev_conditions["category"] = {"$in": category}
            next_conditions["category"] = {"$in": category}
        # 이전 글 조회 (현재 날짜보다 이전 날짜의 첫 번째 글)
        prev_news = await collection_news_list.model.find_one(prev_conditions,
            sort=[("news_date", 1)]
        )
        news_index = await collection_news_list.count_documents(prev_conditions,"news_date"
        )
        page_num = news_index//10 + 1
        # 다음 글 조회 (현재 날짜보다 이후 날짜의 첫 번째 글)
        next_news = await collection_news_list.model.find_one(next_conditions,
            sort=[("news_date", -1)]
        )
        
        return templates.TemplateResponse(
            "news_detail.html",
            {
                "request": request,
                "news": news,
                "prev_news": prev_news,
                "next_news": next_news,
                'search_type':search_type,
                'keyword':keyword,
                'selected_category':category or [],
                'page_num':page_num
            }
        )
        
    except (ValueError, InvalidId):
        raise HTTPException(status_code=400, detail="Invalid news ID format")
    except Exception as e:
        print(f"Error in news_detail: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/report_detail/{news_id}")
async def news_detail(request: Request, news_id: str,search_type: Optional[str]=None,keyword: Optional[str]=None,category: List[str] = Query(None)):
    try:
        # 문자열 ID를 PydanticObjectId로 변환
        object_id = PydanticObjectId(news_id)
        
        # 현재 뉴스 조회
        news = await collection_report_list.get(object_id)

        
        if news is None:
            raise HTTPException(status_code=404, detail="News not found")
        
        # 현재 뉴스의 날짜 가져오기
        current_date = news.news_date
        prev_conditions = {"news_date": {"$gt": current_date},"_id": {"$ne": object_id}}
        next_conditions = {"news_date": {"$lt": current_date},"_id": {"$ne": object_id}}
        if keyword and search_type:
            prev_conditions[search_type] = {"$regex": keyword, "$options": "i"}
            next_conditions[search_type] = {"$regex": keyword, "$options": "i"}
        if category:
            prev_conditions["category"] = {"$in": category}
            next_conditions["category"] = {"$in": category}
        # 이전 글 조회 (현재 날짜보다 이전 날짜의 첫 번째 글)
        prev_news = await collection_report_list.model.find_one(prev_conditions,
            sort=[("news_date", 1)]
        )
        news_index = await collection_report_list.count_documents(prev_conditions,"news_date"
        )
        page_num = news_index//10 + 1
        # 다음 글 조회 (현재 날짜보다 이후 날짜의 첫 번째 글)
        next_news = await collection_report_list.model.find_one(next_conditions,
            sort=[("news_date", -1)]
        )
        
        return templates.TemplateResponse(
            "report_detail.html",
            {
                "request": request,
                "news": news,
                "prev_news": prev_news,
                "next_news": next_news,
                'search_type':search_type,
                'keyword':keyword,
                'selected_category':category or [],
                'page_num':page_num
            }
        )
    except (ValueError, InvalidId):
        raise HTTPException(status_code=400, detail="Invalid news ID format")
    except Exception as e:
        print(f"Error in news_detail: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    
@app.get("/") # 펑션 호출 방식
async def list_get(request:Request):
    await request.form()
    today = datetime.now()
    yesterday = today - timedelta(days=2)
    today_str = today.strftime("%Y/%m/%d")
    yesterday_str = yesterday.strftime("%Y/%m/%d")

    conditions = {"notice_class": {"$regex": '입찰 공고', "$options": "i"}}     
    notice_list= await collection_g2b_notice_list.get_condition_limit(conditions,5,"start_date")
    conditions = {"notice_class": {"$regex": '사전 규격', "$options": "i"}}     
    preparation_list= await collection_g2b_notice_list.get_condition_limit(conditions,5,"start_date")
    
    return templates.TemplateResponse("main.html", {
        "request": request,
        "notice_list": notice_list,
        "preparation_list": preparation_list,
        'today':today_str,
        'yesterday':yesterday_str,
        
    })