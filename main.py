from fastapi import FastAPI               
app = FastAPI()
from typing import Optional

from databases.connections import Settings,Database
from beanie import PydanticObjectId
import datetime
from bson.errors import InvalidId  # 이 부분 추가

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
from models.seoul_institute import seoul_institute
collection_seoul_institute = Database(seoul_institute)
from models.statistic_bank import statistic_bank
collection_statistic_bank = Database(statistic_bank)
from models.venture_doctors import venture_doctors
collection_venture_doctors = Database(venture_doctors)


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



templates = Jinja2Templates(directory="templates/")    

# 메인 페이지로 이동
# @app.get("/")                     
# async def main_get(request: Request):
#     # 현재 페이지 번호 가져오기 (기본값 1)
#     current_page = int(request.query_params.get('page', 1))
    
#     # 빈 conditions 딕셔너리로 전체 데이터 조회
#     conditions = {}
    
#     # getsbyconditionswithpagination 메서드 사용
#     result = await collection_ict_news.getsbyconditionswithpagination(
#         conditions=conditions,
#         page_number=current_page
#     )
    
#     # 결과가 튜플(documents, pagination)인 경우와 아닌 경우 처리
#     if isinstance(result, tuple):
#         items, pagination = result
#     else:
#         items = []
#         pagination = result
    
#     return templates.TemplateResponse("main.html", {
#         'request': request,
#         'items': items,
#         'pagination': pagination
#     })

@app.get("/news/") # 펑션 호출 방식
@app.get("/news/{page_number}") # 펑션 호출 방식
async def list_get(request:Request, page_number: Optional[int]=1):
    await request.form()
    conditions = {} 
    # try :
    #     search_word = transfer_type["transfer_cate"]
    # except:
    #     search_word = None
    # if search_word:     # 검색어 작성
    #     conditions = {"transfer_cate" : { '$regex': search_word}}
    total_list_pagination, pagination = await collection_ict_news.getsbyconditionswithpagination(conditions
                                                                     ,page_number)
    return templates.TemplateResponse(name="main.html", context={'request':request,
                                                                 'items':total_list_pagination,
                                                                 'pagination':pagination})


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

@app.get("/detail/{news_id}")
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
        "main.html",
        {
            "request": request,
            "items": total_list_pagination,
            "pagination": pagination,
            "keyword": keyword,
            "category": category
        }
    )

# # 로그인 페이지로 이동
# @app.get("/login")                     
# async def login_get(request:Request):
#     print(dict(request._query_params))
#     user_list = await collection_user_list.get_all()
    
#     print(user_list)
#     list_user_id = []
#     list_user_email = []
#     list_user_pswd = []
#     for i in range(len(user_list)):
#         list_user_id.append(dict(user_list[i])["id"])
#         list_user_email.append(dict(user_list[i])["user_email"])
#         list_user_pswd.append(dict(user_list[i])["user_password"])
#     print(list_user_id)
#     print(list_user_email)
#     print(list_user_pswd)
#     pass
#     return templates.TemplateResponse("login.html",{'request':request,
#                                                     'user_id':list_user_id,
#                                                     'user_email': list_user_email,
#                                                     'user_pswd': list_user_pswd})

# # @app.post("/login")
# # async def login_post(request:Request):
# #     await request.form()
# #     print(dict(await request.form()))
# #     return templates.TemplateResponse(name="users/list.html", context={'request':request})


# # 로그인 확인 페이지로 이동
# @app.post("/login_check")
# async def login_post(request:Request):
#     await request.form()
#     print(dict(await request.form()))
#     user_list = await collection_user_list.get_all()
#     print(user_list)
#     email_list = []
#     password_list = []
#     for i in range(len(user_list)):
#         email_list.append(user_list[i].user_email)
#         password_list.append(user_list[i].user_password)
#     print(email_list)
#     if dict(await request.form())["login_email"] in email_list: 
#         user_index = email_list.index(dict(await request.form())["login_email"])
#         if password_list[user_index] == dict(await request.form())["login_password"]:
#             link = "login_complete.html"  
#             user_dict = user_list[user_index]
#             return templates.TemplateResponse(name=link, context={'request':request,
#                                                                   'user_dict' : user_dict})
#         else:
#             link = "login_fail.html"
#             return templates.TemplateResponse(name=link, context={'request':request})

#     else:
#         link = "login_fail.html"
#         return templates.TemplateResponse(name=link, context={'request':request})

# # 회원가입 완료시 
# @app.post("/login_insert")                      
# async def login_insert_post(request:Request):
#     user_dict = dict(await request.form())
#     print(dict(await request.form()))
#     user_list = await collection_user_list.get_all()
#     list_user_email = []
#     list_user_name = []
#     for i in range(len(user_list)):
#         list_user_email.append(dict(user_list[i])["user_email"])
#         list_user_name.append(dict(user_list[i])["user_name"])
#     pass
#     if user_dict["user_email"] in list_user_email :     
#         return templates.TemplateResponse("insert_email_error.html",{'request':request})
#     elif user_dict["user_password"] != user_dict["password_check"]:
#         return templates.TemplateResponse("insert_password_error.html",{'request':request})
#     elif user_dict["user_name"] in list_user_name:
#         return templates.TemplateResponse("insert_name_error.html",{'request':request})
        
#     else:
#         user = User_list(**user_dict)
#         await collection_user_list.save(user)
#         return templates.TemplateResponse("insert_interesting_region.html",{'request':request,
#                                                                   'user_dict' : user_dict}) # login.html

# # 커뮤니티 페이지로 이동
# @app.get("/community")                     
# async def community_get(request:Request):
#     print(dict(request._query_params))
#     return templates.TemplateResponse("community.html",{'request':request})

# @app.post("/community")                      
# async def community_post(request:Request):
#     await request.form()
#     print(dict(await request.form()))
#     return templates.TemplateResponse("community.html",{'request':request})

# # 회원가입 페이지로 이동
# @app.get("/insert")                     
# async def insert_get(request:Request):
#     print(dict(request._query_params))
#     return templates.TemplateResponse("insert.html",{'request':request})

# @app.post("/insert")                      
# async def insert_post(request:Request):
#     await request.form()
#     print(dict(await request.form()))
#     return templates.TemplateResponse("insert.html",{'request':request})