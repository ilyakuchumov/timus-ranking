import collections
import re
import os.path
from urllib.request import urlopen

from tqdm import tqdm

from datetime import datetime

import pandas

SUBMIT_ID_KEY = 'submit_id'
DATE_KEY = 'date'
AUTHOR_ID_KEY = 'author_id'
PROBLEM_ID_KEY = 'problem_id'
LANGUAGE_KEY = 'language'
JUDGEMENT_RESULT_KEY = 'judgement_result'
TEST_NUMBER_KEY = 'test_number'
EXECUTION_TIME_KEY = 'execution_time'
MEMORY_USED_KEY = 'memory_used'


class SubmitRecord:
    def __init__(self,
                 submit_id,         # type: int
                 date,              # type: datetime
                 author_id,         # type: int
                 problem_id,        # type: int
                 language,          # type: str
                 judgement_result,  # type: str
                 test_number,       # type: int
                 execution_time,    # type: float
                 memory_used        # type: int
                 ):
        self.submit_id = submit_id
        self.date = date
        self.author_id = author_id
        self.problem_id = problem_id
        self.language = language
        self.judgement_result = judgement_result
        self.test_number = test_number
        self.execution_time = execution_time
        self.memory_used = memory_used

    def to_dict(self):
        return {
            SUBMIT_ID_KEY: self.submit_id,
            DATE_KEY: self.date,
            AUTHOR_ID_KEY: self.author_id,
            PROBLEM_ID_KEY: self.problem_id,
            LANGUAGE_KEY: self.language,
            JUDGEMENT_RESULT_KEY: self.judgement_result,
            TEST_NUMBER_KEY: self.test_number,
            EXECUTION_TIME_KEY: self.execution_time,
            MEMORY_USED_KEY: self.memory_used
        }
    
    def to_list(self):
        as_dict = self.to_dict()
        return [
            as_dict[column]
            for column in SubmitRecord.get_columns()
        ]
    
    @staticmethod
    def get_columns():
        return [
            SUBMIT_ID_KEY,
            DATE_KEY,
            AUTHOR_ID_KEY,
            PROBLEM_ID_KEY,
            LANGUAGE_KEY,
            JUDGEMENT_RESULT_KEY,
            TEST_NUMBER_KEY,
            EXECUTION_TIME_KEY,
            MEMORY_USED_KEY,
        ]

    def __str__(self):
        return str(self.to_dict())

    def __repr__(self):
        return str(self.to_dict())

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return self.to_dict() == other.to_dict()
    

def fetch_result_page(start_id,
                      count
                      ):
    query = 'http://acm.timus.ru/status.aspx?space=1&from={}&count={}'.format(start_id, count)
    return urlopen(query).read().decode('utf-8')


def parse_timus_time(time,
                     date
                     ):
    full_string = date + ' ' + time
    return datetime.strptime(full_string, '%d %b %Y %H:%M:%S')


def parse_timus_execution_time(text):
    try:
        return float(text)
    except ValueError:
        return 0


def parse_single_submit_record(html):
    usual_pattern = (
       r'<TR class=".*?">'
       r'<TD class="id">(.*?)<\/TD>'
       r'<TD class="date"><NOBR>(.*?)<\/NOBR><BR><NOBR>(.*?)<\/NOBR><\/TD>'
       r'<TD class="coder"><A HREF="author.aspx[?]id=(.*?)">.*?<\/A><\/TD>'
       r'<TD class="problem"><A HREF="problem.aspx[?]space=1&amp;num=(.*?)">.*?<SPAN CLASS="problemname">.*?<\/SPAN><\/A><\/TD>'
       r'<TD class="language">(.*?)<\/TD>'
       r'<TD class="verdict_.*?">(.*?)<\/TD>'
       r'<TD class="test">(.*?)<\/TD>'
       r'<TD class="runtime">(.*?)<\/TD>'
       r'<TD class="memory">(.*?) KB<\/TD>'
       r'<\/TR>'
    )
    compilation_error_pattern = (
        r'<TR class=".*?">'
        r'<TD class="id">(.*?)<\/TD>'
        r'<TD class="date"><NOBR>(.*?)<\/NOBR><BR><NOBR>(.*?)<\/NOBR><\/TD>'
        r'<TD class="coder"><A HREF="author.aspx[?]id=(.*?)">.*?<\/A><\/TD>'
        r'<TD class="problem"><A HREF="problem.aspx[?]space=1&amp;num=(.*?)">.*?<SPAN CLASS="problemname">.*?<\/SPAN><\/A><\/TD>'
        r'<TD class="language">(.*?)<\/TD>'
        r'<TD class="verdict_.*?">(.*?)<\/TD>'
        r'<TD class="test"><BR>(.*?)<\/TD>'
        r'<TD class="runtime"><BR>(.*?)<\/TD>'
        r'<TD class="memory"><BR>(.*?)<\/TD>'
        r'<\/TR>'
    )

    is_compilation_error = ('Compilation error' in html)
    
    pattern = usual_pattern if not is_compilation_error else compilation_error_pattern
    search_result = re.search(pattern, html)
    if not search_result:
        return
    groups = search_result.groups()
    
    return SubmitRecord(
        submit_id=int(groups[0]),
        date=parse_timus_time(groups[1], groups[2]),
        author_id=int(groups[3]),
        problem_id=int(groups[4]),
        language=groups[5],
        judgement_result=groups[6] if not is_compilation_error else 'Compilation error',
        test_number=int(groups[7]) if groups[7] not in ['', '<BR>'] else 0,
        execution_time=parse_timus_execution_time(groups[8]),
        memory_used=int(re.sub('\s+', '', groups[9])) if groups[9] else 0
    )


def parse_submit_records(html):
    html = html.replace('\n', '')
    submit_records = []
    for single_raw_submit_record in re.findall(r'<TR.*?>.*?</TR>', html):
        submit_record = parse_single_submit_record(single_raw_submit_record)
        if submit_record:
            submit_records.append(submit_record)
    return submit_records


def fetch_submit_records(start_id,
                         count,
                        ):
    page = fetch_result_page(start_id=start_id, count=count)
    return parse_submit_records(html=page)


def extend_timus(timus_file,
                 submits_per_query=10**3,
                 requests_number=10**3,
                 ):
    new_data = collections.defaultdict(list)
    used = set()
    current_start_id = 0
    
    current_timus = None
    if os.path.exists(timus_file):
        current_timus = pandas.read_csv(timus_file, index_col=0)
        for submit_id in current_timus['submit_id']:
            used.add(submit_id)
        
    if used:
        current_start_id = max(used)
    
    for it in tqdm(range(requests_number)):
        try:
            records = fetch_submit_records(start_id=current_start_id, count=submits_per_query)
        except:
            print('failed to fetch: start_id={} count={}'.format(current_start_id, submits_per_query))
            current_start_id += submits_per_query
            continue
        for record in reversed(records):
            if record.submit_id in used:
                continue
            used.add(record.submit_id)
            record_as_dict = record.to_dict()
            for key in record_as_dict:
                new_data[key].append(record_as_dict[key])
        current_start_id += submits_per_query
    
    new_timus = pandas.DataFrame(data=new_data)
    timuses = []
    if current_timus is not None:
        timuses.append(current_timus)
    timuses.append(new_timus)
    extended_timus = pandas.concat(timuses).reset_index(drop=True)
    extended_timus.to_csv(timus_file)
    return extended_timus
