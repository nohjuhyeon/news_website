from typing import Any, List, Optional
from beanie import init_beanie, PydanticObjectId
from motor.motor_asyncio import AsyncIOMotorClient 
from pydantic_settings import BaseSettings 
from models.ict_news import ict_news
from models.report_list import report_list
from models.statistic_bank import statistic_bank
from models.venture_doctors import venture_doctors
from models.g2b_notice_list import g2b_notice_list
from models.g2b_preparation_list import g2b_preparation_list
from models.news_list import news_list
from utils.paginations import Paginations

class Settings(BaseSettings):                                                                                  
    DATABASE_URL: Optional[str] = None                                              
    CONTAINER_PREFIX: Optional[str] = None 
    
    async def initialize_database(self):                                         
        client = AsyncIOMotorClient(self.DATABASE_URL)                             
        await init_beanie(database=client.get_default_database(),                  
                          document_models=[ict_news, report_list, statistic_bank, venture_doctors, g2b_notice_list, g2b_preparation_list,news_list])

        
    class Config:
        env_file = ".env"                                                

class Database : 
    # model 즉 collection
    def __init__(self, model) -> None:
        self.model = model
        pass

    # 전체 리스트
    async def get_all(self) :
        documents = await self.model.find_all().to_list()         
        pass
        return documents
    
    # 상세 보기
    async def get(self, id: PydanticObjectId) -> Any: 
        doc = await self.model.get(id)               
        if doc:                                  
            return doc
        return False
    
    # 저장
    async def save(self, document) -> None:
        await document.create()
        return None
    
    # 업데이트
    async def update_one(self, id: PydanticObjectId, dic) -> Any:
        doc = await self.model.get(id)
        if doc:
            for key, value in dic.items():
                setattr(doc, key, value)
            await doc.save()
            return True
        return False
    
    # 삭제
    async def delete_one(self, id: PydanticObjectId) -> bool:
        doc = await self.model.get(id)
        if doc:
            await doc.delete()
            return True
        return False

    async def getsbyconditions(self, conditions:dict) -> [Any]:
        documents = await self.model.find(conditions).to_list()  # find({})
        if documents:
            return documents
        return False    
    
    async def getsbyconditionswithpagination(self, conditions:dict, page_number, sort_conditions: str = "news_date", records_per_page=10) -> tuple:
        total = await self.model.find(conditions).count()
        pagination = Paginations(total_records=total, current_page=page_number, records_per_page=records_per_page)
        documents = await self.model.find(conditions).sort([(sort_conditions, -1)]).skip(pagination.start_record_number-1).limit(pagination.records_per_page).to_list()
        return documents, pagination  # 반드시 두 값을 반환해야 함