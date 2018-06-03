import numpy


def filter_timus_by_unique_accepted(timus,
                                    accepted_filter_per_author
                                   ):
    return (
        timus[timus.judgement_result == 'Accepted']
            .groupby('author_id')
            .filter(lambda group: accepted_filter_per_author(len(set(group['problem_id']))))
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


def build_solved_matrix(timus):
    authors_encoder = Encoder(timus['author_id'])
    problems_encoder = Encoder(timus['problem_id'])
    solved_matrix = numpy.zeros((authors_encoder.get_set_size(), problems_encoder.get_set_size()))
    for author_id, problem_id in zip(timus['author_id'], timus['problem_id']):
        encoded_author_id = authors_encoder.encode(author_id)
        encoded_problem_id = problems_encoder.encode(problem_id)
        solved_matrix[encoded_author_id][encoded_problem_id] = 1
    return solved_matrix, authors_encoder, problems_encoder
    

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
