import datetime
import logging

import numpy
import scipy.special


logger = logging.getLogger(__name__)


ACCEPTED_KEY = 'Accepted'
COMPILATION_ERROR_KEY = 'Compilation error'


DEFAULT_START_DATE = datetime.datetime(2018, 6, 4)
DEFAULT_TESTING_DATES = []
for i in range(12):
    DEFAULT_TESTING_DATES.append(
        DEFAULT_START_DATE - datetime.timedelta(days=180 * (i + 1))
    )


def filter_timus_by_unique_accepted(timus,
                                    accepted_filter_per_author
                                   ):
    return (
        timus
            .groupby('author_id')
            .filter(
                lambda group: accepted_filter_per_author(len(set(group[group['judgement_result'] == 'Accepted']['problem_id'])))
            )
    )

    
class TestCase(object):
    def __init__(self,
                 timus,
                 cut_date
                ):
        self.timus = timus
        self.cut_date = cut_date
        
    def get_train(self):
        return self.timus[self.timus['date'] < str(self.cut_date)]
    
    def get_test(self):
        return self.timus[self.timus['date'] >= str(self.cut_date)]


class Encoder(object):
    def __init__(self, values=None):
        self.value_to_code = dict()
        self.code_to_value = dict()
        if values is not None:
            for value in values:
                self.encode(value)
    
    def encode(self, value):
        if value not in self.value_to_code:
            code = len(self.value_to_code)
            self.value_to_code[value] = code
            self.code_to_value[code] = value
            return code
        return self.value_to_code[value]
    
    def decode(self, code):
        return self.code_to_value[code]
    
    def get_set_size(self):
        return len(self.value_to_code)


def build_solved_matrix(timus,
                        enable_negative=False,
                       ):
    def f(x, scale=0.1):
        if x == 1:
            return 1
        if x == 0:
            return 0
        return 1 + -scipy.special.expit(-x * scale) * 2
    
    f = numpy.vectorize(f, otypes=['float64'])
    
    authors_encoder = Encoder(timus['author_id'])
    problems_encoder = Encoder(timus['problem_id'])
    solved_matrix = numpy.zeros((authors_encoder.get_set_size(), problems_encoder.get_set_size()))
    for author_id, problem_id, judgement_result in zip(timus['author_id'], timus['problem_id'], timus['judgement_result']):
        encoded_author_id = authors_encoder.encode(author_id)
        encoded_problem_id = problems_encoder.encode(problem_id)
        if judgement_result == ACCEPTED_KEY:
            solved_matrix[encoded_author_id][encoded_problem_id] = 1
        elif enable_negative and judgement_result != COMPILATION_ERROR_KEY and solved_matrix[encoded_author_id][encoded_problem_id] != 1:
            solved_matrix[encoded_author_id][encoded_problem_id] -= 1
    return f(solved_matrix), authors_encoder, problems_encoder
    

class SingleSuggest(object):
    def __init__(self,
                 problem_index,
                 score,
                ):
        self.problem_index = problem_index
        self.score = score

    def __repr__(self):
        return 'Suggest[problem_index = {}, score = {}]'.format(
            self.problem_index,
            self.score
        )
    
    def __str__(self):
        return self.__repr__()


def get_first_ac_by_author(timus):
    only_accepted = timus[timus['judgement_result'] == 'Accepted']
    first_accepted = only_accepted.sort_values('date').groupby('author_id').first().reset_index()
    next_accepted = dict()
    for author_id, problem_id in zip(first_accepted['author_id'], first_accepted['problem_id']):
        next_accepted[author_id] = problem_id
    return next_accepted


def get_suggest_score(suggest_by_author,
                      next_accepted_by_author
                     ):
    stoped_count = 0
    good_count = 0
    bad_count = 0
    
    for author in suggest_by_author:
        if author not in next_accepted_by_author:
            stoped_count += 1
            continue
        next_accepted = next_accepted_by_author[author]
        is_good = any([
            single_suggest.problem_index == next_accepted
            for single_suggest in suggest_by_author[author]
        ])
        if is_good:
            good_count += 1
        else:
            bad_count += 1
            
    logger.info(
        'good_count = %s bad_count = %s stoped_count = %s',
        good_count,
        bad_count,
        stoped_count
    )
    
    return good_count / (good_count + bad_count)


def get_algorithm_scores(timus,
                         suggest_for_timus,
                         testing_dates=DEFAULT_TESTING_DATES,
                        ):
    scores = []
    for date in testing_dates:
        test_case = TestCase(
            timus=timus,
            cut_date=date
        )
        suggestions = suggest_for_timus(test_case.get_train())
        next_accepted = get_first_ac_by_author(test_case.get_test())
        single_score = get_suggest_score(suggestions, next_accepted)
        scores.append(single_score)
    return numpy.array(scores)
