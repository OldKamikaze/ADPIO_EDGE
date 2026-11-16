from sqlmodel    import Session, create_engine, select, delete
from pathlib import Path

from sqlmodel.ext.asyncio.session import AsyncSession

#sqlite:///:memory: (or, sqlite://)
#sqlite:///relative/path/to/file.db
#sqlite:////absolute/path/to/file.db
#json_deserializer: Callable[..., Any] = ...,
#json_serializer: Callable[..., Any] = ...,     

#db = SQLAlchemy(session_options={"autoflush": False})
#connect_args={"check_same_thread": False},
#poolclass=StaticPool,

# async with AsyncSession(engine) as session:

class engine_db:
    def __init__(self, db_addr, model, name="database"): 
        self.db_addr   = db_addr
        self.engine    = None
        self.name      = name
        self.model     = model

        self.db_debug  = False

        print(f"{self.db_addr} Data Base Initilized")  

  
    def initialize(self, create_model = True, connect_args={"check_same_thread": False}):
        self.engine = create_engine(
            self.db_addr, 
            connect_args=connect_args, 
        )    #,echo=True)

        if create_model: self.model.metadata.create_all(self.engine)

        if self.db_debug: print(f"{self.db_addr} Data Base Initilized")  


    def add_record_na(self, record): #Not Async
        with Session(self.engine) as session:
            session.add(record)
            session.commit()


    def add_records_na(self, records): #Not Async
        if len(records) == 0: return 

        with Session(self.engine) as session:
            [ session.add(rec) for rec in records ]                
            session.commit()


    async def add_record(self, record):
        with Session(self.engine) as session:
            session.add(record)
            session.commit()


    async def add_records(self, records):
        if len(records) == 0: return 

        with Session(self.engine) as session:
            [ session.add(rec) for rec in records ]                
            session.commit()


    async def get_record(self, model, key, value, to_json = False):
        with Session(self.engine) as session:
            record = session.exec(
                select(model).where(key == value)
            ).first() 
        
            if (to_json): return record.to_json() 
            return record
    

    async def get_records(self, model, key, value, to_json = False, order_by_asc=None, order_by_desc=None, limit=0):
        with Session(self.engine) as session:
            sql_req = select(model).where(key == value)
            
            if order_by_asc  : sql_req = sql_req.order_by(order_by_asc.asc())
            if order_by_desc : sql_req = sql_req.order_by(order_by_desc.desc())
            if limit > 0: sql_req = sql_req.limit(limit)

            records  = session.exec( sql_req ).all() 

            if (to_json): return [rec.to_json() for rec in records]
            return records 


    async def get_records_multi(self, model, key, values, to_json = False):
        with Session(self.engine) as session:
            reslt = []

            for val in values:
                record = session.exec( select(model).where(key == val) ).first()         
                if (to_json): record = record.to_json() 
                reslt.append(record)

            return reslt


    async def get_records_range(self, model, key, value, key_range, start, end, to_json = False, order_by_asc=None, order_by_desc=None, limit=0):
        with Session(self.engine) as session:
            sql_req = select(model).where(key == value, key_range >= start, key_range <= end)

            if order_by_asc  : sql_req = sql_req.order_by(order_by_asc.asc())
            if order_by_desc : sql_req = sql_req.order_by(order_by_desc.desc())
            if limit > 0: sql_req = sql_req.limit(limit)

            records  = session.exec( sql_req ).all() 

            if (to_json): return [rec.to_json() for rec in records]
            return records


    async def get_all_records(self, model, to_json = False, order_by_asc=None, order_by_desc=None, limit=0):
        with Session(self.engine) as session:
            sql_req = select(model)
            
            if order_by_asc  : sql_req = sql_req.order_by(order_by_asc.asc())
            if order_by_desc : sql_req = sql_req.order_by(order_by_desc.desc())
            if limit > 0: sql_req = sql_req.limit(limit)

            records  = session.exec( sql_req ).all() 

        if (to_json): return [rec.to_json() for rec in records]        
        return records
    

    async def update_record(self, updated_record, key, value, to_json = False):
        with Session(self.engine) as session:           
            record = session.exec(
                select(type(updated_record)).where(key == value)
            ).first()

            if record == None: 
                session.commit()
                return None
            
            for dict in record.__dict__:
                if dict == "_sa_instance_state": continue
                record.__setattr__(dict, updated_record.__getattribute__(dict))

            session.commit()
            session.refresh(record)

            if to_json == True: return record.to_json()            
            return record
        

    async def update_records(self, updated_records, key):
        with Session(self.engine) as session:
            for updated_record in updated_records:                
                record = session.exec(
                    select(type(updated_record)).where(key == updated_record.id)
                ).first()

                if record == None: 
                    session.commit()
                    return None

                for dict in record.__dict__:
                    if dict == "_sa_instance_state": continue
                    record.__setattr__(dict, updated_record.__getattribute__(dict)) 

            session.commit()     


    async def update_records_with_autocreate(self, updated_records, key):
        with Session(self.engine) as session:
            for updated_record in updated_records:                
                record = session.exec(
                    select(type(updated_record)).where(key == updated_record.id)
                ).first()

                if record == None:
                    session.add(updated_record)
                else:
                    for dict in record.__dict__:
                        val =  updated_record.__getattribute__(dict)
                        if dict == "_sa_instance_state" or val == None or val =={} or val == []: continue #do not chenge filed if = None
                        record.__setattr__(dict, val) 

            session.commit() 


    async def update_fields(self, model, key, value, fields, to_json = False): #files = {"fieldname": "123"}, etc
        with Session(self.engine) as session:           
            record = session.exec(
                select(model).where(key == value)
            ).first()

            if record == None: 
                session.commit()
                return None

            for fld in fields.keys():
                record.__setattr__(fld, fields[fld])

            session.commit()
            session.refresh(record)

            if to_json == True: return record.to_json()            
            return record
        

    async def update_multi_fields(self, model, key, field_key, fields): #files = [{key: val, "fieldname": "123"},] etc
        with Session(self.engine) as session:
            for item in fields:
                record = session.exec(
                    select(model).where(key == item[field_key])
                ).first()

                if record == None: 
                    session.commit()
                    return None

                dict = record.__dict__

                for fld in item.keys():
                    if fld in dict: 
                        record.__setattr__(fld, item[fld])

            session.commit()


    async def delete_record(self, model, key, value):
        with Session(self.engine) as session:           
            record = session.exec(
                select(model).where(key == value)
            ).first()

            if record == None: 
                session.commit()
                return None

            if record != None: session.delete(record)
            session.commit()


    async def delete_records(self, model, key, values):
        with Session(self.engine) as session:
            for value in values:          
                record = session.exec(
                    select(model).where(key == value)
                ).first()

                if record == None: 
                    session.commit()
                    return None

                if record != None: session.delete(record)
                
            session.commit()            


    async def delete_all_records(self, model):
        with Session(self.engine) as session:
            session.exec(delete(model))
            session.commit() 


    async def delete_records_recursively(self, model, key, value):
        with Session(self.engine) as session:        
            records = session.exec(
                select(model).where(key == value)
            ).all()
            
            for record in records:
                if record != None: session.delete(record)
                
            session.commit()             


    def terminate(self):
        if self.db_debug: print(f"{self.db_addr} Data Base Terminated")  
        self.engine.dispose()
