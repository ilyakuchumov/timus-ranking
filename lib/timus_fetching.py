import re
import urllib2

from datetime import datetime


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
            'submit_id': self.submit_id,
            'date': self.date,
            'author_id': self.author_id,
            'problem_id': self.problem_id,
            'language': self.language,
            'judgement_result': self.judgement_result,
            'test_number': self.test_number,
            'execution_time': self.execution_time,
            'memory_used': self.memory_used
        }

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
    return urllib2.urlopen(query).read()


def parse_timus_time(time,
                     date
                     ):
    full_string = date + ' ' + time
    return datetime.strptime(full_string, '%d %b %Y %H:%M:%S')


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
        execution_time=float(groups[8]) if groups[8] else 0,
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
