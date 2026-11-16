import sys
import os
import asyncio
from pathlib  import Path

from typing   import Any, Dict
from datetime import datetime

from sqlalchemy.orm  import registry
from sqlmodel        import Field, SQLModel, StaticPool
from lib.database_sql.sqlmodel_driver import engine_db

from lib.globals  import WORKSPACE, VIRTUAL_SPACE


class terminal_model(SQLModel, registry=registry(), checkfirst=False): #terminal_model model
    pass


class terminal_rec(terminal_model, table=True):
    date    : datetime  =  Field(default_factory = datetime.now, primary_key = True)
    rec_src : str       =  Field(max_length = 16  , default = 'nosrc'      )  #Sourcse, app or system
    text    : str       =  Field(max_length = 2048, default = 'notext'     ) 

    def to_json(self):
        return {
            "date"     :  str(self.date).split('.')[0], 
            "rec_src"  :  self.rec_src,                    
            "text"     :  self.text,              
        }


class _terminalIOSTD:
    def __init__(self, database: engine_db, rec_src: str):
        self.database: engine_db = database
        self.rec_sec             = rec_src         


    def write(self, lines:str):
        if len(lines) > 1:
            self.database.add_record_na( terminal_rec (
                rec_src = self.rec_sec,
                text    = lines.strip().rstrip()[:2046]
            ))
        

    def writelines(self, lines):
        self.write(lines)
            
    def isatty(self):
        return False
    
    def close(self):
        pass

    def fileno(self):
        return 0
    
    def flush(self):
        pass

    def closed(self):
        return False
        

class _terminal_web:
    def __init__(self):
        self.terminalIO   = None

        self.out_std      = None
        self.err_std      = None

        self.record_src   = 'no_src'
        self.virtual      = False      #Shared Memory?

        self.database     = None


    def initialize(self,  record_src: str, virtual: bool):
        self.record_src   = record_src
        self.virtual      = virtual      #Shared Memory?     

        if virtual:
            self.database = engine_db(f"sqlite:///{VIRTUAL_SPACE}{Path('/adpio_terminal.db')}", terminal_model)
        else:
            self.database = engine_db(f"sqlite:///{WORKSPACE}{Path('/adpio_terminal.db')}"    , terminal_model)
        
        self.database.initialize()
        
        self.terminalIO = _terminalIOSTD( self.database, self.record_src )

        self.out_std = sys.stdout #Save System stdouts
        self.err_std = sys.stderr #Save System stdouts
   
        sys.stdout = self.terminalIO
        sys.stderr = self.terminalIO       


    def terminate(self):
        sys.stdout = self.out_std #put sys stdouts back
        sys.stderr = self.err_std #put sys stdouts back

    
    def clear_virtual_db(self):
        try:
            pth = Path(f'{VIRTUAL_SPACE}/adpio_terminal.db')
            if pth.exists():
                os.remove(pth)
        except:
            print('Failed to delete virtual database')


terminal_web: _terminal_web = _terminal_web()
