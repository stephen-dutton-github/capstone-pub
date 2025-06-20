import os
import sqlite3
import json
import asyncio
import aiofiles
import glob
from typing import BinaryIO
from api.services.data_manager import DataManager
from pydantic import BaseModel, ValidationError
from pydantic.dataclasses import dataclass

@dataclass
class Admission:
    subject_id: int
    first_name : str
    family_name : str
    hadm_id : int
    admittime : str
    anchor_age : int
    seq_num : int
    icd_code : str
    icd_version : int
    long_title : str

    def __repr__(self) -> str:
        return f"Admission(subject_id={self.subject_id}, first_name={self.first_name}, family_name={self.family_name}, hadm_id={self.hadm_id}, admittime={self.admittime}, anchor_age={self.anchor_age}, seq_num={self.seq_num}, icd_code={self.icd_code}, icd_version={self.icd_version}, long_title={self.long_title}, notes={self.notes})"

    def __str__(self):
        return self.__repr__()
    


@dataclass
class Patient:
    first_name: str
    family_name: str
    anchor_age: int
    anchor_year: int
    subject_id: int

    def __repr__(self) -> str:
        return f"Patient(subject_id={self.subject_id}, first_name={self.first_name}, family_name={self.family_name}, anchor_age={self.anchor_age}, anchor_year={self.anchor_year})"

    def __str__(self) -> str:
        return self.__repr__()



class PatientServices(DataManager):

    def __init__(self, file_locator: str, readonly: bool = False) -> None:
        super().__init__(file_locator, readonly)
        pass

    def get_admissions(self) -> list[Admission]:
        """
        Returns all admissions from the 'admissions' table in the SQLite database.
        Use a count of 533 in testing to ensure all admissions are returned with a primary and secondary diagnosis.
        """
        # Adjust this query as needed (e.g., add filters, LIMIT, etc.)
        query = """
            select 	pat.subject_id, 
					pinf.first_name,
					pinf.family_name,
                    adm.hadm_id, 
                    adm.admittime, 
                    pat.anchor_age, 
                    diag.seq_num, 
                    diag.icd_code,
                    diag.icd_version, 
                    dscr.long_title
            from patients pat
            inner join admissions 	 	adm	  on pat.subject_id = adm.subject_id
            inner join diagnoses_icd 	diag on pat.subject_id = diag.subject_id and adm.hadm_id = diag.hadm_id
            inner join d_icd_diagnoses	dscr on diag.icd_code = dscr.icd_code and diag.seq_num < 2
			inner join d_patients_info	pinf on pat.subject_id = pinf.subject_id
            order by pat.subject_id
        """

        sql_results = self.execute_sql(query)
        cast_results = []
        for result in sql_results:
            try:
                admission = Admission(**result)
                cast_results.append(admission)
            except ValidationError as e:
                print(f"Validation error for row: {result}")
                print(e.json())
        return cast_results


    def get_icds(self, subject_id: str):
        query = """
                WITH last_admits AS (
                SELECT
                    subject_id,
                    MAX(admittime) AS max_admit
                FROM admissions
                GROUP BY subject_id
                )
                SELECT m.icd_code, o.icd_version, o.long_title
                FROM admissions a
                JOIN last_admits l 	ON a.subject_id = l.subject_id	AND a.admittime = l.max_admit
                JOIN diagnoses_icd m ON a.subject_id = m.subject_id AND a.hadm_id = m.hadm_id
                JOIN d_icd_diagnoses o	ON m.icd_code = o.icd_code
                WHERE a.subject_id =  {sid}""".format(sid = subject_id)
        sql_results = self.execute_sql(query)
        cast_results =  [result for result in sql_results]
        return cast_results

    async def get_notes(self, 
                        subject_id : str, 
                        base_path : str = "/app/api/services/notes") -> dict[str, str]:
        """
        Load multiple files matching a glob pattern asynchronously in binary mode.
        
        Args:
            pattern: Glob pattern string to match file paths.

        Returns:
            A dictionary mapping file paths to their binary contents.
        """
        query = """
                WITH last_admits AS (
                SELECT
                    subject_id,
                    MAX(admittime) AS max_admit
                FROM admissions
                GROUP BY subject_id
                )
                SELECT a.subject_id, a.hadm_id
                FROM admissions a
                JOIN last_admits l 	ON a.subject_id = l.subject_id	AND a.admittime = l.max_admit
                WHERE a.subject_id =  {sid}
                LIMIT 1""".format(sid = subject_id)
        sql_results = self.execute_sql(query)
        
        file_contents = {}
        hadm_id = sql_results[0]["hadm_id"]
        pattern = os.path.join(base_path, f"{subject_id}_{hadm_id}.txt")
        for filepath in glob.glob(pattern):
            async with aiofiles.open(filepath, mode='r') as f:  # DON'T use rb access qualifier
                content = await f.read()
                file_reference = (filepath
                                  .replace(base_path,"")
                                  .replace(r"/","")
                                  )
                file_contents[file_reference] = content
        return file_contents


    async def get_xrays(self, 
                        subject_id : str, 
                        base_path : str = "/app/api/services/xray") -> dict[str, bytes]:
        """
        Load multiple files matching a glob pattern asynchronously in binary mode.
        
        Args:
            pattern: Glob pattern string to match file paths.

        Returns:
            A dictionary mapping file paths to their binary contents.
        """
        query = """
                WITH last_admits AS (
                SELECT
                    subject_id,
                    MAX(admittime) AS max_admit
                FROM admissions
                GROUP BY subject_id
                )
                SELECT a.subject_id, a.hadm_id
                FROM admissions a
                JOIN last_admits l 	ON a.subject_id = l.subject_id	AND a.admittime = l.max_admit
                WHERE a.subject_id =  {sid}
                LIMIT 1""".format(sid = subject_id)
        
        sql_results = self.execute_sql(query)
        
        file_contents = {}
        hadm_id = sql_results[0]["hadm_id"]
        file_contents = {}
        pattern = os.path.join(base_path, f"{subject_id}_{hadm_id}.jpg")
        for filepath in glob.glob(pattern):
            async with aiofiles.open(filepath, mode='rb') as f:
                content = await f.read()
                file_reference = (filepath
                                  .replace(base_path,"")
                                  .replace(r"/","")
                                  )
                file_contents[file_reference] = content
        return file_contents

    def get_subject_id(self, first_name : str, last_name: str):
        """
        Returns all patient subject_id entries from the 'patients' table in the SQLite database.
        Use a count of 100 in testing to ensure 100 subject_id entries are returned.
        """
        first_name = first_name.lower()
        last_name = last_name.lower()
        null_subject = {"subject_id":-1}

        # Adjust this query as needed (e.g., add filters, LIMIT, etc.)
        query = """
            SELECT DISTINCT p.subject_id
            FROM patients p INNER JOIN d_patients_info pinf 
                            ON p.subject_id = pinf.subject_id
            WHERE pinf.first_name 
            LIKE '{fn}%' 
            AND pinf.family_name LIKE '{ln}%'
            LIMIT 1
        """.format(fn = first_name,ln = last_name)

        sql_results = self.execute_sql(query)
        cast_results =  [result for result in sql_results]

        if len(cast_results) < 1:
            cast_results.append(null_subject)
            
        return cast_results

    def get_subject_ids(self):
        """
        Returns all patient subject_id entries from the 'patients' table in the SQLite database.
        Use a count of 100 in testing to ensure 100 subject_id entries are returned.
        """
        # Adjust this query as needed (e.g., add filters, LIMIT, etc.)
        query = """
            select distinct subject_id
            from patients
            order by subject_id
        """
        sql_results = self.execute_sql(query)
        cast_results =  [result for result in sql_results]
        return cast_results
    
    
    def patients(self) -> list[Patient]:
        """
        Returns all patient subject_id entries from the 'patients' table in the SQLite database.
        Use a count of 100 in testing to ensure 100 subject_id entries are returned.
        """
        # Adjust this query as needed (e.g., add filters, LIMIT, etc.)
        query = """
            select 	p.subject_id, 
                    pinf.first_name, 
                    pinf.family_name,
                    p.anchor_age, 
                    p.anchor_year
            from patients p
            inner join d_patients_info pinf on p.subject_id = pinf.subject_id
        """
        sql_results = self.execute_sql(query)
        cast_results = []
        for result in sql_results:
                try:
                    patient = Patient(**result)
                    cast_results.append(patient)
                except ValidationError as e:
                    print(f"Validation error for row: {result}")
                    print(e.json())
        return cast_results 
    

    def search_by_subject_id(self, subject_id: str):
        """
        Search for the 'patients' table in the SQLite database.
        Using subjectg ID "10000032" in testing to ensure "Aarav Sharma" is returned.
        """
        # Adjust this query as needed (e.g., add filters, LIMIT, etc.)
        query = f"""
            select 	p.subject_id as subject_id, 
                    pinf.first_name as first_name, 
                    pinf.family_name as family_name,
                    p.anchor_age as anchor_age, 
                    p.anchor_year as anchor_year
            from patients p
            inner join d_patients_info pinf on p.subject_id = pinf.subject_id
            where p.subject_id = '{subject_id}';
            """
        
        sql_results= self.execute_sql(query)
        cast_results = [Patient(**result) for result in  sql_results]
        return cast_results