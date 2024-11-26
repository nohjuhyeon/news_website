from fastapi import FastAPI               
app = FastAPI()
from typing import Optional

from databases.connections import Settings,Database
from beanie import PydanticObjectId
import datetime
from bson.errors import InvalidId  # 이 부분 추가
from typing import List
from fastapi import Query
settings = Settings()
@app.on_event("startup")
async def init_db():
    await settings.initialize_database()


# from routes.admin import router as admin_router                   

from fastapi import Request                                
from fastapi.templating import Jinja2Templates              
# from utils.paginations import Paginations

from models.ict_news import ict_news # 컬랙션을 연결하고, 컬렉션에 저장/불러오기 하는 방법 
collection_ict_news = Database(ict_news)  
from models.report_list import report_list
collection_report_list = Database(report_list)
from models.statistic_bank import statistic_bank
collection_statistic_bank = Database(statistic_bank)
from models.venture_doctors import venture_doctors
collection_venture_doctors = Database(venture_doctors)
from models.g2b_notice_list import g2b_notice_list
collection_g2b_notice_list = Database(g2b_notice_list)
from models.g2b_preparation_list import g2b_preparation_list
collection_g2b_preparation = Database(g2b_preparation_list)
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
        "selected_notice_types": notice_type or []
    })


@app.post("/")                      
async def main_post(request:Request):
    await request.form()
    print(dict(await request.form()))
    venture_doctors_list = await collection_venture_doctors.get_all()
    
    return templates.TemplateResponse("main.html",{'request':request,
                                                    'items': venture_doctors_list})

# 기존 import문 아래에 추가
from fastapi import HTTPException
from beanie import PydanticObjectId

# 뉴스 상세 페이지 라우트 추가

@app.get("/news_detail/{news_id}")
async def news_detail(request: Request, news_id: str):
    try:
        # 문자열 ID를 PydanticObjectId로 변환
        object_id = PydanticObjectId(news_id)
        
        # 현재 뉴스 조회
        news = await collection_ict_news.get(object_id)
        
        if news is None:
            raise HTTPException(status_code=404, detail="News not found")
        
        # 현재 뉴스의 날짜 가져오기
        current_date = news.news_date
        
        # 이전 글 조회 (현재 날짜보다 이전 날짜의 첫 번째 글)
        prev_news = await collection_ict_news.model.find_one(
            {
                "news_date": {"$lt": current_date},
                "_id": {"$ne": object_id}
            },
            sort=[("news_date", -1)]
        )
        
        # 다음 글 조회 (현재 날짜보다 이후 날짜의 첫 번째 글)
        next_news = await collection_ict_news.model.find_one(
            {
                "news_date": {"$gt": current_date},
                "_id": {"$ne": object_id}
            },
            sort=[("news_date", 1)]
        )
        
        return templates.TemplateResponse(
            "news_detail.html",
            {
                "request": request,
                "news": news,
                "prev_news": prev_news,
                "next_news": next_news
            }
        )
        
    except (ValueError, InvalidId):
        raise HTTPException(status_code=400, detail="Invalid news ID format")
    except Exception as e:
        print(f"Error in news_detail: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/report_detail/{news_id}")
async def news_detail(request: Request, news_id: str):
    try:
        # 문자열 ID를 PydanticObjectId로 변환
        object_id = PydanticObjectId(news_id)
        
        # 현재 뉴스 조회
        news = await collection_seoul_institute.get(object_id)
        
        if news is None:
            raise HTTPException(status_code=404, detail="News not found")
        
        # 현재 뉴스의 날짜 가져오기
        current_date = news.news_date
        
        # 이전 글 조회 (현재 날짜보다 이전 날짜의 첫 번째 글)
        prev_news = await collection_seoul_institute.model.find_one(
            {
                "news_date": {"$lt": current_date},
                "_id": {"$ne": object_id}
            },
            sort=[("news_date", -1)]
        )
        
        # 다음 글 조회 (현재 날짜보다 이후 날짜의 첫 번째 글)
        next_news = await collection_seoul_institute.model.find_one(
            {
                "news_date": {"$gt": current_date},
                "_id": {"$ne": object_id}
            },
            sort=[("news_date", 1)]
        )
        
        return templates.TemplateResponse(
            "news_detail.html",
            {
                "request": request,
                "news": news,
                "prev_news": prev_news,
                "next_news": next_news
            }
        )
        
    except (ValueError, InvalidId):
        raise HTTPException(status_code=400, detail="Invalid news ID format")
    except Exception as e:
        print(f"Error in news_detail: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 뉴스 검색 기능 추가 (옵션)
@app.get("/news/search/")
async def search_news(
    request: Request,
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    page: int = 1
):
    conditions = {}
    
    # 검색 조건 설정
    if keyword:
        conditions["$or"] = [
            {"news_title": {"$regex": keyword, "$options": "i"}},
            {"news_content": {"$regex": keyword, "$options": "i"}},
            {"news_keywords": {"$regex": keyword, "$options": "i"}}
        ]
    
    if category:
        conditions["category"] = {"$in": [category]}
    
    # 데이터 조회
    total_list_pagination, pagination = await collection_ict_news.getsbyconditionswithpagination(
        conditions=conditions,
        page_number=page
    )
    
    return templates.TemplateResponse(
        "news_list.html",
        {
            "request": request,
            "items": total_list_pagination,
            "pagination": pagination,
            "keyword": keyword,
            "category": category
        }
    )
