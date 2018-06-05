from . import utils

from multiprocessing.pool import ThreadPool


def suggest(timus,
            top_count,
            problem_difficulties
           ):
    solved_matrix, authors_encoder, problems_encoder = utils.build_solved_matrix(timus)
    suggestions = dict()
    
    def process(author_id):
        suggestions = []
        for problem_id in range(problems_encoder.get_set_size()):
            if solved_matrix[author_id][problem_id] == 1:
                continue
            real_problem_id = problems_encoder.decode(problem_id)
            suggestions.append(
                utils.SingleSuggest(
                    problem_index=real_problem_id,
                    score=problem_difficulties[real_problem_id]
                )
            )
        return sorted(suggestions, key=lambda s: s.score, reverse=True)[:top_count]
    
    with ThreadPool() as pool:
        return {
            authors_encoder.decode(author_id): suggestions
            for author_id, suggestions in enumerate(pool.map(process, range(authors_encoder.get_set_size())))
        }
