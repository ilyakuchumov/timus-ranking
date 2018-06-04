import pandas
import numpy

from multiprocessing.pool import ThreadPool

from . import utils


def item_based_suggest(user_id,
                       top_count,
                       solved_matrix,
                       problems_similarity
                      ):
    problems_count = solved_matrix.shape[1]
    solved_problems = set()
    unsolved_problems = dict()
    for problem_id in range(problems_count):
        if solved_matrix[user_id][problem_id] == 0:
            unsolved_problems[problem_id] = 0
        else:
            solved_problems.add(problem_id)
    
    for solved_problem_id in solved_problems:
        for unsolved_problem_id in unsolved_problems:
            unsolved_problems[unsolved_problem_id] = max(unsolved_problems[unsolved_problem_id], problems_similarity[unsolved_problem_id][solved_problem_id])
            
    suggestions = [
        utils.SingleSuggest(
            problem_index=problem_id,
            score=unsolved_problems[problem_id]
        )
        for problem_id in unsolved_problems
    ]
    
    return sorted(suggestions, key=lambda s: s.score, reverse=True)[:top_count]


def suggest(timus,
            top_count,
           ):
    solved_matrix, authors_encoder, problems_encoder = utils.build_solved_matrix(timus)
    problems_similarity = numpy.corrcoef(solved_matrix, rowvar=False)
    
    def process(user_id):
        return item_based_suggest(
            user_id=user_id,
            top_count=top_count,
            solved_matrix=solved_matrix,
            problems_similarity=problems_similarity,
        )
    
    with ThreadPool() as pool:
        all_suggestions = list(pool.map(process, range(solved_matrix.shape[0])))
        
    suggestions = dict()
    for user_index, suggest in enumerate(all_suggestions):
        suggestions[authors_encoder.decode(user_index)] = [
            utils.SingleSuggest(
                problem_index=problems_encoder.decode(suggestion.problem_index),
                score=suggestion.score
            )
            for suggestion in all_suggestions[user_index]
        ]
    return suggestions
