from typing import Optional, List                   # 데이터베이스와 연결하거나 데이터를 상호작용할 때 사용
from datetime import datetime
from beanie import Document, Link                   # 데이터베이스의 데이터를 문서나 링크 형태로 가져올 수 있는 기능을 제공
# from pydantic import BaseModel, EmailStr

# 개발자 실수로 들어가는 field 제한
class seoul_institute(Document) :  # 상속을 위한 것                 # 데이터 베이스에서 이용할 값들을 설정
    news_title : Optional[str] = None 
    news_content : Optional[str] = None 
    news_date : Optional[datetime] = None
    news_link : Optional[str] = None
    news_topic : Optional[str] = None
    first_summary : Optional[str] = None
    full_summary : Optional[str] = None
    category : List[str] = None
    news_keywords : List[str] = None
    class Settings :   
        name = "seoul_institute"  # collection의 이름